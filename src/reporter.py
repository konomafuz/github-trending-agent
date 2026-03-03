"""
src/reporter.py

Generate a Markdown report from enriched repos + Gemini analyses.
Writes to reports/YYYY-MM-DD.md and returns the file path.
"""

import logging
import os
from datetime import date
from pathlib import Path

logger = logging.getLogger(__name__)

REPORTS_DIR = Path(__file__).parent.parent / "reports"

_STARS_MAP = {5: "⭐⭐⭐⭐⭐", 4: "⭐⭐⭐⭐", 3: "⭐⭐⭐", 2: "⭐⭐", 1: "⭐", 0: "—"}
_COMPLEXITY_EMOJI = {"easy": "🟢", "medium": "🟡", "hard": "🔴"}


def _stars_emoji(score: int) -> str:
    return _STARS_MAP.get(score, "—")


def _complexity_emoji(text: str) -> str:
    low = text.lower()
    for key, emoji in _COMPLEXITY_EMOJI.items():
        if key in low:
            return f"{emoji} {text}"
    return text


def _fmt_number(n: int) -> str:
    if n >= 1000:
        return f"{n:,}"
    return str(n)


def _nav_table(repos: list[dict], analysis_map: dict[str, dict]) -> str:
    rows = ["| 排名 | 仓库 | 语言 | Stars | 今日增长 | 商业化评分 |",
            "|------|------|------|-------|---------|-----------|"]
    sorted_repos = sorted(
        repos,
        key=lambda r: analysis_map.get(r["full_name"], {}).get("shang_ye_hua_qian_li", 0),
        reverse=True,
    )
    for rank, repo in enumerate(sorted_repos, 1):
        fn = repo["full_name"]
        ana = analysis_map.get(fn, {})
        score = ana.get("shang_ye_hua_qian_li", 0)
        lang = repo.get("language") or "—"
        stars = _fmt_number(repo.get("stars", 0))
        today = f"+{_fmt_number(repo.get('stars_today', 0))}" if repo.get("stars_today") else "—"
        rows.append(f"| {rank} | {fn} | {lang} | {stars} | {today} | {_stars_emoji(score)} |")
    return "\n".join(rows)


def _repo_section(repo: dict, ana: dict) -> str:
    fn = repo["full_name"]
    html_url = repo.get("html_url", f"https://github.com/{fn}")
    lang = repo.get("language") or "—"
    topics = repo.get("topics", [])
    topics_str = " ".join(f"`{t}`" for t in topics[:6]) if topics else ""
    stars = _fmt_number(repo.get("stars", 0))
    forks = _fmt_number(repo.get("forks", 0))
    today = f"+{_fmt_number(repo.get('stars_today', 0))}" if repo.get("stars_today") else "—"

    score = ana.get("shang_ye_hua_qian_li", 0)
    er_ci = ana.get("er_ci_kai_fa", [])
    er_ci_lines = "\n".join(f"{i}. {item}" for i, item in enumerate(er_ci, 1))

    complexity_raw = ana.get("ji_shu_fu_za_du", "—")

    lines = [
        f"### [{fn}]({html_url})",
        "",
        f"`{lang}` {topics_str}",
        f"**Stars**: {stars} | **今日新增**: {today} | **Forks**: {forks}",
        "",
        "| 维度 | 分析 |",
        "|------|------|",
        f"| **功能定位** | {ana.get('gong_neng_ding_wei', '—')} |",
        f"| **商业化潜力** | {_stars_emoji(score)} ({score}/5) |",
        f"| **竞品SaaS** | {ana.get('jing_pin_saas', '—')} |",
        f"| **目标客户** | {ana.get('mu_biao_ke_hu', '—')} |",
        f"| **技术复杂度** | {_complexity_emoji(complexity_raw)} |",
        "",
        "**二次开发方向**:",
        er_ci_lines,
        "",
        f"> **推荐行动**: {ana.get('tui_jian_xing_dong', '—')}",
        "",
        "---",
        "",
    ]
    return "\n".join(lines)


def generate_report(
    repos: list[dict],
    analyses: list[dict],
    report_date: date | None = None,
) -> str:
    """
    Build the full Markdown report, write it to reports/YYYY-MM-DD.md,
    and return the file path as a string.
    """
    if report_date is None:
        report_date = date.today()

    date_str = report_date.strftime("%Y-%m-%d")
    date_zh = report_date.strftime("%Y年%m月%d日")

    analysis_map: dict[str, dict] = {a["full_name"]: a for a in analyses}

    # Sort repos by score desc for detail sections
    sorted_repos = sorted(
        repos,
        key=lambda r: analysis_map.get(r["full_name"], {}).get("shang_ye_hua_qian_li", 0),
        reverse=True,
    )

    sections = [
        f"# GitHub Trending 商业化分析报告",
        f"> 日期：{date_zh} | 分析数量：{len(repos)} 个高潜力仓库",
        "",
        "## 快速导航 - 商业化潜力排行",
        "",
        _nav_table(repos, analysis_map),
        "",
        "## 详细分析",
        "",
    ]

    for repo in sorted_repos:
        fn = repo["full_name"]
        ana = analysis_map.get(fn, {})
        sections.append(_repo_section(repo, ana))

    content = "\n".join(sections)

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    out_path = REPORTS_DIR / f"{date_str}.md"
    out_path.write_text(content, encoding="utf-8")
    logger.info("Report written to %s", out_path)
    return str(out_path)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    dummy_repos = [
        {
            "full_name": "shadcn/ui",
            "html_url": "https://github.com/shadcn/ui",
            "language": "TypeScript",
            "topics": ["react", "components"],
            "stars": 82000,
            "forks": 5000,
            "stars_today": 1234,
            "description": "UI components",
        }
    ]
    dummy_analyses = [
        {
            "full_name": "shadcn/ui",
            "gong_neng_ding_wei": "可复制粘贴的 React UI 组件库",
            "shang_ye_hua_qian_li": 5,
            "jing_pin_saas": "v0.dev $20/mo，TailwindUI $299一次性",
            "er_ci_kai_fa": [
                "定制化组件商店（按需付费 $5-20/组件包）",
                "针对特定行业的完整 UI 套件（医疗/金融 $99/mo）",
                "托管式组件文档站服务（$29/mo）",
            ],
            "mu_biao_ke_hu": "B2B：独立开发者/外包团队",
            "ji_shu_fu_za_du": "Medium: React + Stripe + 设计能力",
            "tui_jian_xing_dong": "用 3 周时间做一个专注于 SaaS Dashboard 场景的付费组件包，定价 $49",
        }
    ]
    path = generate_report(dummy_repos, dummy_analyses)
    print("Generated:", path)
