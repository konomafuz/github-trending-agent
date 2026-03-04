# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

GitHub Trending 商业化分析 Agent - Automated daily analysis of GitHub trending repositories for commercialization opportunities using Gemini AI.

**Tech Stack**: Python 3.11, Gemini API (gemini-2.5-flash), GitHub REST API, Telegram Bot API, GitHub Actions

**Repository**: https://github.com/konomafuz/github-trending-agent

## Development Commands

### Local Development
```bash
# Install dependencies
pip install -r requirements.txt

# Set up environment (copy and fill in real values)
cp .env.example .env

# Run full pipeline (for testing, set MAX_REPOS=3 for faster validation)
python main.py

# Test individual modules
python -m src.scraper    # Test scraping only
python -m src.enricher   # Test scraping + enrichment
python -m src.analyzer   # Test analysis with dummy data
```

### GitHub Actions
- **Scheduled**: Daily at UTC 02:00 (Beijing 10:00)
- **Manual trigger**: Actions tab → "Daily GitHub Trending Analysis" → Run workflow
- **Required Secrets**: `GEMINI_API_KEY`, `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`

## Architecture

### Five-Stage Pipeline (main.py)

1. **Scraper** (`src/scraper.py`)
   - Scrapes github.com/trending (daily + weekly)
   - Deduplicates by full_name
   - Returns: owner, name, description, language, stars_today, period

2. **Enricher** (`src/enricher.py`)
   - Calls GitHub REST API for each repo
   - Filters by MIN_STARS (default 1000)
   - Caps at MAX_REPOS (default 25)
   - Adds: stars, forks, license, topics, readme_excerpt (first 1500 chars)

3. **Analyzer** (`src/analyzer.py`)
   - **Single batch call** to Gemini API with all repos
   - Returns Chinese analysis with 7 fields per repo:
     - `gong_neng_ding_wei` (功能定位)
     - `shang_ye_hua_qian_li` (商业化潜力, 1-5 score)
     - `jing_pin_saas` (竞品SaaS)
     - `er_ci_kai_fa` (二次开发方向, ≥3 items)
     - `mu_biao_ke_hu` (目标客户)
     - `ji_shu_fu_za_du` (技术复杂度)
     - `tui_jian_xing_dong` (推荐行动)
   - Retries up to 3 times with 10s delay
   - Returns stub analysis on failure to keep pipeline running

4. **Reporter** (`src/reporter.py`)
   - Generates Markdown report in `reports/YYYY-MM-DD.md`
   - Commits to repository via GitHub Actions

5. **Notifier** (`src/notifier.py`)
   - Sends Telegram message with top repos and link to full report

### Key Design Decisions

- **Batch analysis**: All repos sent to Gemini in one call (not per-repo) for efficiency
- **Graceful degradation**: Analyzer returns stub data on failure so pipeline continues
- **Rate limiting**: 0.5s sleep between GitHub API calls in enricher
- **Idempotent commits**: GitHub Actions only commits if report changed

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `GEMINI_API_KEY` | Yes | - | From aistudio.google.com |
| `GEMINI_MODEL` | No | gemini-2.5-flash | Model name |
| `GITHUB_TOKEN` | Recommended | - | For higher rate limits |
| `TELEGRAM_BOT_TOKEN` | No | - | From @BotFather |
| `TELEGRAM_CHAT_ID` | No | - | From @userinfobot |
| `GITHUB_REPO` | No | - | For Telegram link (e.g. "user/repo") |
| `MIN_STARS` | No | 1000 | Filter threshold |
| `MAX_REPOS` | No | 25 | Analysis limit |

## Code Conventions

- Type hints used throughout (Python 3.11+ syntax with `|` for unions)
- Logging via stdlib `logging` module (INFO level)
- Docstrings at module and function level
- Error handling: try/except with logging, graceful fallbacks
- Chinese field names in analysis schema (matches business domain)
