"""
src/analyzer.py

Batch-analyze repos with Gemini API in a single call.
Returns a list of analysis dicts keyed by full_name.

Analysis schema per repo:
    {
        "full_name": str,
        "gong_neng_ding_wei": str,
        "shang_ye_hua_qian_li": int,          # 1-5
        "jing_pin_saas": str,
        "er_ci_kai_fa": list[str],             # ≥3 items
        "mu_biao_ke_hu": str,
        "ji_shu_fu_za_du": str,               # "Easy/Medium/Hard + skills"
        "tui_jian_xing_dong": str,
    }
"""
import json
import logging
import os
import random
import re
import time

from openai import OpenAI

logger = logging.getLogger(__name__)

DEFAULT_MODEL = "deepseek-chat"
MAX_RETRIES = int(os.getenv("DEEPSEEK_MAX_RETRIES", "5"))
RETRY_DELAY = int(os.getenv("DEEPSEEK_RETRY_DELAY_SECONDS", "10"))
RETRY_MAX_DELAY = int(os.getenv("DEEPSEEK_RETRY_MAX_SECONDS", "120"))
PLACEHOLDER_MARKERS = (
    "待分析",
    "待补充",
    "待完善",
    "未提供",
    "暂无",
    "未知",
    "占位",
    "todo",
    "tbd",
    "unknown",
    "none",
    "null",
    "n/a",
)

SYSTEM_PROMPT = """你是一名资深独立开发者和产品商业化顾问，专注于从开源项目中识别 1→100 的商业化机会。
你的分析要具体、可执行，避免空话套话。用中文回答。"""

ANALYSIS_PROMPT_TEMPLATE = """分析以下 GitHub 热门项目的商业化潜力。

输入数据（JSON 数组，每项包含仓库基本信息和 README 摘录）：
{repos_json}

请对每个仓库输出 JSON 分析，严格按照以下格式返回一个 JSON 数组（不要有任何其他文字，不要 markdown 代码块）：
[
  {{
    "full_name": "owner/name",
    "gong_neng_ding_wei": "功能定位，1-2句话",
    "shang_ye_hua_qian_li": 4,
    "jing_pin_saas": "竞品SaaS现状及价格区间",
    "er_ci_kai_fa": [
      "具体可执行的方向1",
      "具体可执行的方向2",
      "具体可执行的方向3"
    ],
    "mu_biao_ke_hu": "B2B/B2C + 具体人群",
    "ji_shu_fu_za_du": "Medium: React + Stripe + 设计能力",
    "tui_jian_xing_dong": "最重要的下一步具体行动"
  }}
]

评分标准（shang_ye_hua_qian_li）：
- 5分：企业级痛点/竞品$100+/mo
- 4分：SMB痛点/竞品$10-100/mo
- 3分：有用但市场拥挤
- 2分：小众技术工具
- 1分：纯库难直接变现

确保 full_name 与输入一致，每个项目至少3条二次开发方向。"""


def _build_repo_payload(repo: dict) -> dict:
    """Build a compact dict to include in the prompt."""
    return {
        "full_name": repo["full_name"],
        "description": repo.get("description", ""),
        "language": repo.get("language") or "Unknown",
        "stars": repo.get("stars", 0),
        "forks": repo.get("forks", 0),
        "topics": repo.get("topics", []),
        "license": repo.get("license") or "Unknown",
        "readme_excerpt": repo.get("readme_excerpt", "")[:800],  # keep prompt size reasonable
    }


def _strip_fences(text: str) -> str:
    """Remove markdown code fences if AI wrapped the JSON."""
    text = text.strip()
    # Remove ```json ... ``` or ``` ... ```
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    return text.strip()


def _is_rate_limited(exc: Exception) -> bool:
    msg = str(exc).lower()
    markers = ("429", "rate limit", "too many requests", "resource exhausted", "quota")
    return any(marker in msg for marker in markers)


def _retry_delay_seconds(attempt: int, exc: Exception) -> float:
    if _is_rate_limited(exc):
        # Exponential backoff + jitter avoids synchronized retries across runs.
        exp_delay = min(RETRY_DELAY * (2 ** (attempt - 1)), RETRY_MAX_DELAY)
        return exp_delay + random.uniform(0, 1)
    return float(RETRY_DELAY)


def _normalize_text(value: object) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _normalize_score(value: object) -> int:
    try:
        score = int(value)
    except (TypeError, ValueError):
        return 0
    return max(0, min(5, score))


def _normalize_actions(value: object) -> list[str]:
    if isinstance(value, list):
        actions = [_normalize_text(v) for v in value]
        return [a for a in actions if a]
    if isinstance(value, str):
        parts = re.split(r"[\n;；]+", value)
        actions = [p.strip(" -•\t") for p in parts]
        return [a for a in actions if a]
    return []


def _normalize_analysis_item(item: dict) -> dict:
    return {
        "full_name": _normalize_text(item.get("full_name")),
        "gong_neng_ding_wei": _normalize_text(item.get("gong_neng_ding_wei")),
        "shang_ye_hua_qian_li": _normalize_score(item.get("shang_ye_hua_qian_li")),
        "jing_pin_saas": _normalize_text(item.get("jing_pin_saas")),
        "er_ci_kai_fa": _normalize_actions(item.get("er_ci_kai_fa")),
        "mu_biao_ke_hu": _normalize_text(item.get("mu_biao_ke_hu")),
        "ji_shu_fu_za_du": _normalize_text(item.get("ji_shu_fu_za_du")),
        "tui_jian_xing_dong": _normalize_text(item.get("tui_jian_xing_dong")),
    }


def _is_placeholder_text(text: str) -> bool:
    value = text.strip()
    if not value:
        return True

    lower = value.lower()
    if lower in {"-", "--", "n/a", "na", "none", "null", "todo", "tbd", "unknown"}:
        return True

    for marker in PLACEHOLDER_MARKERS:
        if marker in lower or marker in value:
            return True
    return False


def _is_meaningful_text(text: str, min_length: int = 6) -> bool:
    return len(text.strip()) >= min_length and not _is_placeholder_text(text)


def _quality_issue(item: dict) -> str | None:
    if not item.get("full_name"):
        return "missing full_name"

    score = item.get("shang_ye_hua_qian_li", 0)
    if not isinstance(score, int) or score < 1 or score > 5:
        return "score must be in range 1-5"

    required_fields = (
        "gong_neng_ding_wei",
        "jing_pin_saas",
        "mu_biao_ke_hu",
        "ji_shu_fu_za_du",
        "tui_jian_xing_dong",
    )
    for field in required_fields:
        if not _is_meaningful_text(item.get(field, "")):
            return f"field `{field}` is empty/placeholder"

    actions = item.get("er_ci_kai_fa", [])
    valid_actions = [a for a in actions if _is_meaningful_text(a, min_length=4)]
    if len(valid_actions) < 2:
        return "field `er_ci_kai_fa` has fewer than 2 valid entries"

    return None


def analyze_repos(
    repos: list[dict],
    api_key: str | None = None,
    model_name: str | None = None,
) -> list[dict]:
    """
    Send all repos in a single API call using OpenAI-compatible SDK for DeepSeek.
    Retries up to MAX_RETRIES times on failure.
    Returns list of analysis dicts; missing repos get a default stub.
    Raises RuntimeError when DeepSeek fully fails so downstream stages stop.
    """
    key = api_key or os.getenv("DEEPSEEK_API_KEY", "")
    if not key:
        raise ValueError("DEEPSEEK_API_KEY not set")

    model = model_name or os.getenv("DEEPSEEK_MODEL", DEFAULT_MODEL)
    
    client = OpenAI(
        api_key=key,
        base_url="https://api.deepseek.com",
    )

    payloads = [_build_repo_payload(r) for r in repos]
    repos_json = json.dumps(payloads, ensure_ascii=False, indent=2)
    prompt = ANALYSIS_PROMPT_TEMPLATE.format(repos_json=repos_json)

    logger.info("Sending %d repos to DeepSeek (%s)…", len(repos), model)

    analyses: list[dict] = []
    last_exc: Exception | None = None

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ],
                response_format={"type": "json_object"} if model == "deepseek-chat" else None,
            )
            raw = response.choices[0].message.content
            cleaned = _strip_fences(raw)
            analyses_dict = json.loads(cleaned)
            # Sometimes json_object format returns an object with a key containing the array
            # We specifically asked for a top-level array in the prompt but let's handle both
            if isinstance(analyses_dict, dict):
                # Try to extract the first list value if it's wrapped
                for v in analyses_dict.values():
                    if isinstance(v, list):
                        analyses = v
                        break
                else:
                    analyses = [analyses_dict]
            elif isinstance(analyses_dict, list):
                analyses = analyses_dict
                
            if not isinstance(analyses, list):
                raise ValueError(f"Expected JSON array, got {type(analyses)}")
            if not analyses:
                raise ValueError("DeepSeek returned an empty analysis array")
            logger.info("DeepSeek returned %d analyses on attempt %d", len(analyses), attempt)
            break
        except Exception as exc:
            last_exc = exc
            if attempt < MAX_RETRIES:
                delay = _retry_delay_seconds(attempt, exc)
                logger.warning(
                    "Attempt %d/%d failed: %s. Retrying in %.1fs",
                    attempt,
                    MAX_RETRIES,
                    exc,
                    delay,
                )
                time.sleep(delay)
            else:
                logger.warning("Attempt %d/%d failed: %s", attempt, MAX_RETRIES, exc)

    if not analyses:
        raise RuntimeError(
            f"All DeepSeek attempts failed; aborting pipeline. Last error: {last_exc}"
        ) from last_exc

    # Index by full_name for easy lookup, and normalize schema first.
    analysis_map: dict[str, dict] = {}
    for idx, item in enumerate(analyses, 1):
        if not isinstance(item, dict):
            logger.warning("DeepSeek item #%d is not a JSON object, ignoring", idx)
            continue
        normalized = _normalize_analysis_item(item)
        fn = normalized["full_name"]
        if not fn:
            logger.warning("DeepSeek item #%d missing full_name, ignoring", idx)
            continue
        analysis_map[fn] = normalized

    # Ensure every input repo has an entry
    result: list[dict] = []
    stubbed: list[str] = []
    for repo in repos:
        fn = repo["full_name"]
        if fn in analysis_map:
            item = dict(analysis_map[fn])
            issue = _quality_issue(item)
            if issue:
                logger.warning("Low-quality analysis for %s (%s), using stub", fn, issue)
                stubbed.append(fn)
                result.append(_stub_analysis(repo))
                continue
            item.setdefault("_is_stub", False)
            result.append(item)
        else:
            logger.warning("No analysis returned for %s, using stub", fn)
            stubbed.append(fn)
            result.append(_stub_analysis(repo))

    if len(stubbed) == len(repos):
        raise RuntimeError(
            "DeepSeek returned no usable analyses for any repo; aborting pipeline."
        )

    return result


def _stub_analysis(repo: dict) -> dict:
    return {
        "full_name": repo["full_name"],
        "gong_neng_ding_wei": repo.get("description", "（分析失败）"),
        "shang_ye_hua_qian_li": 0,
        "jing_pin_saas": "待分析",
        "er_ci_kai_fa": ["待分析"],
        "mu_biao_ke_hu": "待分析",
        "ji_shu_fu_za_du": "待分析",
        "tui_jian_xing_dong": "待分析",
        "_is_stub": True,
    }


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    # Quick smoke test with dummy data
    dummy = [
        {
            "full_name": "shadcn/ui",
            "description": "Beautifully designed components",
            "language": "TypeScript",
            "stars": 82000,
            "forks": 5000,
            "topics": ["react", "components", "ui"],
            "license": "MIT",
            "readme_excerpt": "Re-usable components built using Radix UI and Tailwind CSS.",
        }
    ]
    results = analyze_repos(dummy)
    print(json.dumps(results, ensure_ascii=False, indent=2))
