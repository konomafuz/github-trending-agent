"""
src/enricher.py

Enrich scraped repos with precise data from GitHub REST API:
  - stars, forks, license
  - topics
  - README excerpt (first ~1500 chars, images stripped)

Filters out repos below MIN_STARS and caps at MAX_REPOS.

Enriched item schema extends scraper schema with:
    {
        "stars": int,
        "forks": int,
        "license": str | None,
        "topics": list[str],
        "readme_excerpt": str,
        "html_url": str,
    }
"""

import base64
import logging
import os
import re
import time

import requests

logger = logging.getLogger(__name__)

GITHUB_API = "https://api.github.com"
README_MAX_CHARS = 1500
# Strip markdown image syntax: ![alt](url)
_IMAGE_RE = re.compile(r"!\[[^\]]*\]\([^)]*\)")
# Strip HTML img tags
_HTML_IMG_RE = re.compile(r"<img[^>]*>", re.IGNORECASE)


def _api_headers(token: str | None = None) -> dict:
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    tok = token or os.getenv("GITHUB_TOKEN", "")
    if tok:
        headers["Authorization"] = f"Bearer {tok}"
    return headers


def _get(url: str, headers: dict, params: dict | None = None) -> dict | None:
    try:
        resp = requests.get(url, headers=headers, params=params, timeout=15)
        if resp.status_code == 404:
            return None
        resp.raise_for_status()
        return resp.json()
    except requests.RequestException as exc:
        logger.warning("GitHub API request failed for %s: %s", url, exc)
        return None


def _clean_readme(raw: str) -> str:
    """Decode base64 README, strip images, return first README_MAX_CHARS chars."""
    try:
        decoded = base64.b64decode(raw.replace("\n", "")).decode("utf-8", errors="replace")
    except Exception:
        decoded = raw
    decoded = _IMAGE_RE.sub("", decoded)
    decoded = _HTML_IMG_RE.sub("", decoded)
    return decoded[:README_MAX_CHARS].strip()


def enrich_repos(
    repos: list[dict],
    min_stars: int = 1000,
    max_repos: int = 25,
    token: str | None = None,
) -> list[dict]:
    """
    For each repo, call GitHub API to get full metadata.
    Returns up to max_repos repos with stars >= min_stars, sorted by stars desc.
    """
    headers = _api_headers(token)
    enriched = []

    for i, repo in enumerate(repos):
        full_name = repo["full_name"]
        logger.info("[%d/%d] Enriching %s…", i + 1, len(repos), full_name)

        # --- repo metadata ---
        meta = _get(f"{GITHUB_API}/repos/{full_name}", headers)
        if not meta:
            logger.warning("  Skipping %s (no metadata)", full_name)
            time.sleep(0.5)
            continue

        stars = meta.get("stargazers_count", 0)
        if stars < min_stars:
            logger.info("  Skipping %s (stars=%d < %d)", full_name, stars, min_stars)
            time.sleep(0.5)
            continue

        forks = meta.get("forks_count", 0)
        license_name = (meta.get("license") or {}).get("spdx_id") or None
        html_url = meta.get("html_url", f"https://github.com/{full_name}")

        # --- topics ---
        topics_data = _get(
            f"{GITHUB_API}/repos/{full_name}/topics",
            {**headers, "Accept": "application/vnd.github.mercy-preview+json"},
        )
        topics: list[str] = (topics_data or {}).get("names", [])

        # --- README ---
        readme_data = _get(f"{GITHUB_API}/repos/{full_name}/readme", headers)
        if readme_data and readme_data.get("content"):
            readme_excerpt = _clean_readme(readme_data["content"])
        else:
            readme_excerpt = ""

        enriched.append(
            {
                **repo,
                "stars": stars,
                "forks": forks,
                "license": license_name,
                "topics": topics,
                "readme_excerpt": readme_excerpt,
                "html_url": html_url,
            }
        )
        logger.info("  OK  stars=%d topics=%s", stars, topics[:3])
        time.sleep(0.5)

    # Sort by stars descending, cap at max_repos
    enriched.sort(key=lambda r: r["stars"], reverse=True)
    result = enriched[:max_repos]
    logger.info("Enrichment complete: %d repos (min_stars=%d)", len(result), min_stars)
    return result


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    from src.scraper import fetch_trending

    raw = fetch_trending()
    rich = enrich_repos(raw, min_stars=1000, max_repos=5)
    for r in rich:
        print(r["full_name"], r["stars"], r["topics"][:3])
