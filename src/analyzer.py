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
import re
import time

import google.generativeai as genai

logger = logging.getLogger(__name__)

DEFAULT_MODEL = "gemini-2.5-flash"
MAX_RETRIES = 3
RETRY_DELAY = 10  # seconds between retries

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
    """Remove markdown code fences if Gemini wrapped the JSON."""
    text = text.strip()
    # Remove ```json ... ``` or ``` ... ```
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    return text.strip()


def analyze_repos(
    repos: list[dict],
    api_key: str | None = None,
    model_name: str | None = None,
) -> list[dict]:
    """
    Send all repos in a single Gemini API call.
    Retries up to MAX_RETRIES times on failure.
    Returns list of analysis dicts; missing repos get a default stub.
    """
    key = api_key or os.getenv("GEMINI_API_KEY", "")
    if not key:
        raise ValueError("GEMINI_API_KEY not set")

    model = model_name or os.getenv("GEMINI_MODEL", DEFAULT_MODEL)
    genai.configure(api_key=key)
    gen_model = genai.GenerativeModel(
        model_name=model,
        system_instruction=SYSTEM_PROMPT,
    )

    payloads = [_build_repo_payload(r) for r in repos]
    repos_json = json.dumps(payloads, ensure_ascii=False, indent=2)
    prompt = ANALYSIS_PROMPT_TEMPLATE.format(repos_json=repos_json)

    logger.info("Sending %d repos to Gemini (%s)…", len(repos), model)

    analyses: list[dict] = []
    last_exc: Exception | None = None

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = gen_model.generate_content(prompt)
            raw = response.text
            cleaned = _strip_fences(raw)
            analyses = json.loads(cleaned)
            if not isinstance(analyses, list):
                raise ValueError(f"Expected JSON array, got {type(analyses)}")
            logger.info("Gemini returned %d analyses on attempt %d", len(analyses), attempt)
            break
        except Exception as exc:
            last_exc = exc
            logger.warning("Attempt %d/%d failed: %s", attempt, MAX_RETRIES, exc)
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_DELAY)

    if not analyses:
        logger.error("All Gemini attempts failed. Last error: %s", last_exc)
        # Return stub analyses so pipeline can continue
        analyses = [_stub_analysis(r) for r in repos]

    # Index by full_name for easy lookup
    analysis_map = {a.get("full_name", ""): a for a in analyses}

    # Ensure every input repo has an entry
    result = []
    for repo in repos:
        fn = repo["full_name"]
        if fn in analysis_map:
            result.append(analysis_map[fn])
        else:
            logger.warning("No analysis returned for %s, using stub", fn)
            result.append(_stub_analysis(repo))

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
