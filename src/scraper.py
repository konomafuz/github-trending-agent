"""
src/scraper.py

Scrape github.com/trending (daily + weekly), deduplicate, and pre-filter
repos with stars >= MIN_STARS (default 1000).

Returned item schema:
    {
        "owner": str,
        "name": str,
        "full_name": str,          # "owner/name"
        "description": str,
        "language": str | None,
        "stars_today": int,        # today's gain shown on trending page
        "period": "daily"|"weekly"
    }
"""

import time
import logging
import os
import re

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

TRENDING_URL = "https://github.com/trending"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )
}
RETRY_DELAYS = [5, 10, 20]


def _fetch_with_retry(url: str, params: dict | None = None) -> str:
    """GET url with exponential-backoff retry (3 attempts)."""
    for attempt, delay in enumerate(RETRY_DELAYS, 1):
        try:
            resp = requests.get(url, params=params, headers=HEADERS, timeout=20)
            resp.raise_for_status()
            return resp.text
        except requests.RequestException as exc:
            if attempt == len(RETRY_DELAYS):
                raise
            logger.warning("Attempt %d failed (%s). Retrying in %ds…", attempt, exc, delay)
            time.sleep(delay)
    return ""  # unreachable


def _parse_stars_today(text: str) -> int:
    """Extract integer from strings like '1,234 stars today'."""
    digits = re.sub(r"[^\d]", "", text)
    return int(digits) if digits else 0


def _parse_trending_page(html: str, period: str) -> list[dict]:
    """Parse a single trending page and return a list of repo dicts."""
    soup = BeautifulSoup(html, "html.parser")
    repos = []

    for article in soup.select("article.Box-row"):
        # owner/name
        link_tag = article.select_one("h2.h3 a")
        if not link_tag:
            continue
        href = link_tag.get("href", "").strip("/")
        parts = href.split("/")
        if len(parts) < 2:
            continue
        owner, name = parts[0], parts[1]

        # description
        desc_tag = article.select_one("p")
        description = desc_tag.get_text(strip=True) if desc_tag else ""

        # language
        lang_tag = article.select_one("[itemprop='programmingLanguage']")
        language = lang_tag.get_text(strip=True) if lang_tag else None

        # stars gained today/this week
        stars_span = article.select_one("span.d-inline-block.float-sm-right")
        stars_today = _parse_stars_today(stars_span.get_text()) if stars_span else 0

        repos.append(
            {
                "owner": owner,
                "name": name,
                "full_name": f"{owner}/{name}",
                "description": description,
                "language": language,
                "stars_today": stars_today,
                "period": period,
            }
        )
    return repos


def fetch_trending(min_stars: int = 1000) -> list[dict]:
    """
    Fetch daily + weekly trending repos, deduplicate by full_name,
    and return those that will later pass the stars threshold.
    (Actual star count filtering happens in enricher after API call.)
    """
    results: dict[str, dict] = {}

    for period, since_param in [("daily", "daily"), ("weekly", "weekly")]:
        logger.info("Fetching %s trending…", period)
        html = _fetch_with_retry(TRENDING_URL, params={"since": since_param})
        repos = _parse_trending_page(html, period)
        logger.info("  Found %d repos on %s trending page", len(repos), period)

        for repo in repos:
            key = repo["full_name"].lower()
            if key not in results:
                results[key] = repo
            else:
                # merge: keep the higher stars_today and the 'daily' period tag
                existing = results[key]
                if repo["stars_today"] > existing["stars_today"]:
                    existing["stars_today"] = repo["stars_today"]
                if repo["period"] == "daily":
                    existing["period"] = "daily"

        time.sleep(3)

    deduped = list(results.values())
    logger.info("Total unique repos after dedup: %d", len(deduped))
    return deduped


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    repos = fetch_trending()
    for r in repos[:5]:
        print(r)
