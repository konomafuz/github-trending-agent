"""
src/notifier.py

Send a Telegram message with the Top-5 commercialization opportunities
from today's analysis. Failures are non-fatal (logged, not raised).

Uses only the `requests` library — no Telegram SDK needed.
"""

import logging
import os
from datetime import date

import requests

logger = logging.getLogger(__name__)

TELEGRAM_API = "https://api.telegram.org"
# Telegram MarkdownV2 special chars that must be escaped
_ESCAPE_CHARS = r"_*[]()~`>#+-=|{}.!"


def _escape_mdv2(text: str) -> str:
    """Escape special characters for Telegram MarkdownV2."""
    for ch in _ESCAPE_CHARS:
        text = text.replace(ch, f"\\{ch}")
    return text


def _stars_emoji(score: int) -> str:
    return "⭐" * max(0, min(5, score))


def _build_message(
    top_repos: list[dict],
    analysis_map: dict[str, dict],
    report_date: date,
    github_repo: str,
) -> str:
    """
    Build Telegram MarkdownV2 message with Top-5 summary.
    github_repo: "username/repo-name" of the Actions repo.
    """
    date_str = report_date.strftime("%Y-%m-%d")

    lines = [
        f"📊 *GitHub Trending 商业化日报 {_escape_mdv2(date_str)}*",
        "",
        f"🏆 今日 Top {len(top_repos)} 高潜力项目：",
        "",
    ]

    for i, repo in enumerate(top_repos, 1):
        fn = repo["full_name"]
        ana = analysis_map.get(fn, {})
        score = ana.get("shang_ye_hua_qian_li", 0)
        stars = repo.get("stars", 0)
        stars_fmt = f"{stars:,}"
        action = ana.get("tui_jian_xing_dong", "")
        positioning = ana.get("gong_neng_ding_wei", "")
        competitor = ana.get("jing_pin_saas", "")

        # Escape dynamic content for MarkdownV2
        fn_esc = _escape_mdv2(fn)
        stars_esc = _escape_mdv2(stars_fmt)
        pos_esc = _escape_mdv2(positioning)
        comp_esc = _escape_mdv2(competitor[:60] + ("…" if len(competitor) > 60 else ""))
        action_esc = _escape_mdv2(action[:100] + ("…" if len(action) > 100 else ""))

        lines.append(f"*{i}\\. {_stars_emoji(score)} {fn_esc} \\({stars_esc} stars\\)*")
        lines.append(f"   {pos_esc}")
        if competitor:
            lines.append(f"   竞品: {comp_esc}")
        lines.append(f"   💡 {action_esc}")
        lines.append("")

    # Report link
    if github_repo:
        report_url = f"https://github.com/{github_repo}/blob/main/reports/{date_str}.md"
        report_url_esc = _escape_mdv2(report_url)
        lines.append(f"📄 [完整报告]({report_url_esc})")

    return "\n".join(lines)


def send_telegram(
    top_repos: list[dict],
    analyses: list[dict],
    report_date: date | None = None,
    bot_token: str | None = None,
    chat_id: str | None = None,
    github_repo: str = "",
) -> bool:
    """
    Send Telegram notification. Returns True on success, False on failure.
    Never raises — failures are logged as warnings.
    """
    token = bot_token or os.getenv("TELEGRAM_BOT_TOKEN", "")
    cid = chat_id or os.getenv("TELEGRAM_CHAT_ID", "")

    if not token or not cid:
        logger.warning("Telegram not configured (missing BOT_TOKEN or CHAT_ID). Skipping.")
        return False

    if report_date is None:
        report_date = date.today()

    # Build top-5 from analyses sorted by score
    analysis_map: dict[str, dict] = {a["full_name"]: a for a in analyses}
    sorted_repos = sorted(
        top_repos,
        key=lambda r: analysis_map.get(r["full_name"], {}).get("shang_ye_hua_qian_li", 0),
        reverse=True,
    )[:5]

    message = _build_message(sorted_repos, analysis_map, report_date, github_repo)

    url = f"{TELEGRAM_API}/bot{token}/sendMessage"
    payload = {
        "chat_id": cid,
        "text": message,
        "parse_mode": "MarkdownV2",
        "disable_web_page_preview": True,
    }

    try:
        resp = requests.post(url, json=payload, timeout=15)
        data = resp.json()
        if data.get("ok"):
            logger.info("Telegram message sent successfully")
            return True
        else:
            logger.warning("Telegram API error: %s", data.get("description", data))
            # Fallback: send as plain text
            return _send_plain_fallback(token, cid, sorted_repos, analysis_map, report_date, github_repo)
    except requests.RequestException as exc:
        logger.warning("Telegram request failed: %s", exc)
        return False


def _send_plain_fallback(
    token: str,
    cid: str,
    top_repos: list[dict],
    analysis_map: dict[str, dict],
    report_date: date,
    github_repo: str,
) -> bool:
    """Send a simple plain-text message as fallback."""
    date_str = report_date.strftime("%Y-%m-%d")
    lines = [f"GitHub Trending 商业化日报 {date_str}", ""]
    for i, repo in enumerate(top_repos, 1):
        fn = repo["full_name"]
        ana = analysis_map.get(fn, {})
        score = ana.get("shang_ye_hua_qian_li", 0)
        stars = repo.get("stars", 0)
        action = ana.get("tui_jian_xing_dong", "")
        lines.append(f"{i}. {'⭐'*score} {fn} ({stars:,} stars)")
        lines.append(f"   {action[:100]}")
        lines.append("")

    if github_repo:
        lines.append(f"完整报告: https://github.com/{github_repo}/blob/main/reports/{date_str}.md")

    url = f"{TELEGRAM_API}/bot{token}/sendMessage"
    try:
        resp = requests.post(
            url,
            json={"chat_id": cid, "text": "\n".join(lines), "disable_web_page_preview": True},
            timeout=15,
        )
        ok = resp.json().get("ok", False)
        if ok:
            logger.info("Telegram plain-text fallback sent")
        else:
            logger.warning("Telegram plain-text fallback also failed: %s", resp.text[:200])
        return ok
    except requests.RequestException as exc:
        logger.warning("Telegram fallback request failed: %s", exc)
        return False


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    # Quick test — set env vars before running
    dummy_repos = [
        {"full_name": "shadcn/ui", "stars": 82000, "stars_today": 1234},
    ]
    dummy_analyses = [
        {
            "full_name": "shadcn/ui",
            "gong_neng_ding_wei": "可复制粘贴的 React UI 组件库",
            "shang_ye_hua_qian_li": 5,
            "jing_pin_saas": "v0.dev $20/mo",
            "er_ci_kai_fa": ["定制化组件商店"],
            "mu_biao_ke_hu": "独立开发者",
            "ji_shu_fu_za_du": "Medium",
            "tui_jian_xing_dong": "做付费组件包，定价 $49",
        }
    ]
    ok = send_telegram(dummy_repos, dummy_analyses, github_repo="your-username/github-trending-agent")
    print("Sent:", ok)
