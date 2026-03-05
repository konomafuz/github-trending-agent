# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

GitHub Trending 商业化分析 Agent - Automated daily analysis of GitHub trending repositories for commercialization opportunities using Gemini AI.

**Tech Stack**:
- Backend: Python 3.11, Gemini API (gemini-2.5-flash), GitHub REST API, Telegram Bot API
- Frontend: Vue 3, Vite, TypeScript, Tailwind CSS, Pinia
- Deployment: GitHub Actions, GitHub Pages

**Repository**: https://github.com/konomafuz/github-trending-agent

**Live Site**: https://konomafuz.github.io/github-trending-agent/

## Development Commands

### Local Development

**Backend:**
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

**Frontend:**
```bash
# Install dependencies
cd web
npm install

# Start dev server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview
```

### GitHub Actions
- **Scheduled**: Daily at UTC 02:00 (Beijing 10:00)
- **Manual trigger**: Actions tab → "Daily GitHub Trending Analysis" → Run workflow
- **Required Secrets**: `GEMINI_API_KEY`, `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`

## Architecture

### Backend: Five-Stage Pipeline (main.py)

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

6. **JSON Exporter** (`src/json_exporter.py`)
   - Exports analyzed data to JSON format for web frontend
   - Generates `web/public/data/latest.json`

### Frontend: Vue 3 SPA (web/)

**Pages:**
- **Latest** (`/`): Display latest analysis with new repo highlights
- **Archive** (`/archive`): Multi-dimensional browsing (language, potential, customer, etc.)
- **Favorites** (`/favorites`): User's saved repos (requires GitHub login)

**Key Features:**
- Multi-dimensional categorization (6 dimensions)
- Search and filter functionality
- GitHub OAuth authentication
- Cloud-synced favorites via GitHub Gist
- Responsive design (mobile-friendly)
- Dark/light theme toggle (planned)

**Data Flow:**
```
Python Analysis → JSON Export → Vue Frontend → GitHub Pages
```

### Key Design Decisions

**Backend:**
- **Batch analysis**: All repos sent to Gemini in one call (not per-repo) for efficiency
- **Graceful degradation**: Analyzer returns stub data on failure so pipeline continues
- **Rate limiting**: 0.5s sleep between GitHub API calls in enricher
- **Idempotent commits**: GitHub Actions only commits if report changed
- **Dual output**: Generates both MD reports and JSON for web frontend

**Frontend:**
- **Static deployment**: No backend server needed, fully static on GitHub Pages
- **Client-side rendering**: Vue 3 SPA with client-side routing
- **Cloud storage**: Uses GitHub Gist for favorites (no database needed)
- **Progressive enhancement**: Works without login, enhanced with GitHub auth

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

**Python (Backend):**
- Type hints used throughout (Python 3.11+ syntax with `|` for unions)
- Logging via stdlib `logging` module (INFO level)
- Docstrings at module and function level
- Error handling: try/except with logging, graceful fallbacks
- Chinese field names in analysis schema (matches business domain)

**TypeScript/Vue (Frontend):**
- TypeScript strict mode enabled
- Vue 3 Composition API with `<script setup>`
- Tailwind CSS for styling (utility-first)
- Pinia for state management
- Component naming: PascalCase for files, kebab-case in templates

## Project Structure

```
github-trending-agent/
├── src/              # Python backend
│   ├── scraper.py
│   ├── enricher.py
│   ├── analyzer.py
│   ├── reporter.py
│   ├── notifier.py
│   └── json_exporter.py
├── reports/          # Generated MD reports
├── web/              # Vue 3 frontend
│   ├── src/
│   │   ├── views/    # Page components
│   │   ├── components/  # Reusable components
│   │   ├── stores/   # Pinia stores
│   │   └── router/   # Vue Router config
│   ├── public/
│   │   └── data/     # JSON data files
│   └── dist/         # Built files (deployed to gh-pages)
├── docs/
│   └── plans/        # Design and implementation docs
├── .github/
│   └── workflows/    # GitHub Actions
└── main.py           # Main pipeline orchestrator
```
