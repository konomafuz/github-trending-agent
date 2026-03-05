"""
main.py

Entry point: orchestrates the five pipeline stages.

Usage:
    python main.py

Environment variables (or .env file):
    DEEPSEEK_API_KEY      - required
    DEEPSEEK_MODEL        - optional, default deepseek-chat
    GITHUB_TOKEN        - optional but strongly recommended
    TELEGRAM_BOT_TOKEN  - optional
    TELEGRAM_CHAT_ID    - optional
    GITHUB_REPO         - optional, used for Telegram report link (e.g. "user/repo")
    MIN_STARS           - optional, default 1000
    MAX_REPOS           - optional, default 25
    MAX_STUB_RATIO      - optional, default 0.2 (abort if stub analyses exceed ratio)
"""

import logging
import os
import sys
from datetime import date
from pathlib import Path

# Load .env for local development (no-op in GitHub Actions where env vars are set directly)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from src.scraper import fetch_trending
from src.enricher import enrich_repos
from src.analyzer import analyze_repos
from src.reporter import generate_report
from src.notifier import send_telegram
from src.json_exporter import export_to_json

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


def main() -> int:
    min_stars = int(os.getenv("MIN_STARS", "1000"))
    max_repos = int(os.getenv("MAX_REPOS", "25"))
    max_stub_ratio = float(os.getenv("MAX_STUB_RATIO", "0.2"))
    github_repo = os.getenv("GITHUB_REPO", "")
    today = date.today()

    logger.info("=" * 60)
    logger.info("GitHub Trending Analysis — %s", today)
    logger.info("min_stars=%d  max_repos=%d", min_stars, max_repos)
    logger.info("=" * 60)

    # ── Stage 1: Scrape ─────────────────────────────────────────
    logger.info("[1/5] Scraping GitHub Trending…")
    raw_repos = fetch_trending(min_stars=min_stars)
    if not raw_repos:
        logger.error("No repos scraped. Aborting.")
        return 1

    # ── Stage 2: Enrich ─────────────────────────────────────────
    logger.info("[2/5] Enriching %d repos via GitHub API…", len(raw_repos))
    enriched = enrich_repos(
        raw_repos,
        min_stars=min_stars,
        max_repos=max_repos,
        token=os.getenv("GITHUB_TOKEN"),
    )
    if not enriched:
        logger.error("No repos passed enrichment filter. Aborting.")
        return 1
    logger.info("  → %d repos after enrichment", len(enriched))

    # ── Stage 3: Analyze ────────────────────────────────────────
    logger.info("[3/5] Analyzing with DeepSeek…")
    try:
        analyses = analyze_repos(
            enriched,
            api_key=os.getenv("DEEPSEEK_API_KEY"),
            model_name=os.getenv("DEEPSEEK_MODEL"),
        )
    except Exception as exc:
        logger.error("Analysis stage failed. Aborting before report generation: %s", exc)
        return 1
    logger.info("  → %d analyses returned", len(analyses))
    stub_count = sum(1 for a in analyses if a.get("_is_stub"))
    stub_ratio = (stub_count / len(analyses)) if analyses else 1.0
    if stub_ratio > max_stub_ratio:
        logger.error(
            "Analysis quality gate failed: %d/%d stubs (%.1f%%) > MAX_STUB_RATIO=%.1f%%. Aborting.",
            stub_count,
            len(analyses),
            stub_ratio * 100,
            max_stub_ratio * 100,
        )
        return 1

    # ── Stage 4: Report ─────────────────────────────────────────
    logger.info("[4/5] Generating Markdown report…")
    report_path = generate_report(enriched, analyses, report_date=today)
    logger.info("  → Report: %s", report_path)

    # Export to JSON for web frontend
    logger.info("Exporting data to JSON...")
    # Merge enriched repos with analyses
    analysis_map = {a["full_name"]: a for a in analyses}
    analyzed_repos = []
    for repo in enriched:
        merged = {**repo}
        if repo["full_name"] in analysis_map:
            merged["analysis"] = analysis_map[repo["full_name"]]
        analyzed_repos.append(merged)
    export_to_json(analyzed_repos)
    logger.info("JSON export complete")

    # ── Stage 5: Notify ─────────────────────────────────────────
    logger.info("[5/5] Sending Telegram notification…")
    send_telegram(
        top_repos=enriched,
        analyses=analyses,
        report_date=today,
        github_repo=github_repo,
    )

    logger.info("=" * 60)
    logger.info("Pipeline complete. Report saved to: %s", report_path)
    logger.info("=" * 60)
    return 0


if __name__ == "__main__":
    sys.exit(main())
