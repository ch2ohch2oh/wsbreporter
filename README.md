# WSB Reporter

A tool to fetch and summarize Reddit posts from r/wallstreetbets using a configurable LLM, and generate a static website of the letters.

## Setup

1.  **Install dependencies**:
    ```bash
    uv sync
    ```

2.  **Configure API keys**:
    Copy the example environment file and fill in your Reddit and LLM API credentials:
    ```bash
    cp .env.example .env
    # Edit .env with your keys
    ```

    Scraped posts, comments, snapshots, and generated markdown reports are stored
    in SQLite. The scraper can run every few hours, while the reporter compares
    the latest post snapshots against the previous generated report. By default
    the database lives at:
    ```env
    DATABASE_PATH=data/wsbreporter.sqlite3
    COMMENT_REFRESH_HOURS=2
    REPORT_COMMENTS_PER_POST=12
    REPORT_MAX_BODY_WORDS=220
    REPORT_EDIT_PASS=0
    REPORT_WITH_NEWS=0
    NEWS_STALE_HOURS=6
    NEWS_MAX_TERMS=8
    NEWS_ITEMS_PER_TERM=3
    ```

    Gemini is the default provider:
    ```env
    LLM_PROVIDER=gemini
    GEMINI_API_KEY=...
    GEMINI_MODEL_NAME=gemini-3-flash-preview
    ```

    DeepSeek is supported through its OpenAI-compatible API:
    ```env
    LLM_PROVIDER=deepseek
    DEEPSEEK_API_KEY=...
    DEEPSEEK_MODEL_NAME=deepseek-chat
    DEEPSEEK_BASE_URL=https://api.deepseek.com
    ```

    OpenAI is also supported:
    ```env
    LLM_PROVIDER=openai
    OPENAI_API_KEY=...
    OPENAI_MODEL_NAME=gpt-4o-mini
    ```

    For other OpenAI-compatible providers:
    ```env
    LLM_PROVIDER=openai-compatible
    OPENAI_COMPATIBLE_API_KEY=...
    OPENAI_COMPATIBLE_BASE_URL=https://provider.example.com/v1
    OPENAI_COMPATIBLE_MODEL_NAME=provider-model-name
    ```

## Usage

If you have `just` installed, common workflows are available as short targets:

```bash
just scrape
just report
just daily
just site
```

### 1. Generate a Letter
Fetched posts are summarized into a markdown letter. You can save it directly to the site content directory:

```bash
# Generate today's letter
uv run python -m wsbreporter.pipeline --markdown-output site/markdown/$(date +%Y-%m-%d).md
```

Scraping and report generation can also be run separately:

```bash
# Scrape Reddit into SQLite only
uv run python -m wsbreporter.scraper

# Generate a report from the latest stored SQLite data only
uv run python -m wsbreporter.reporter --markdown-output site/markdown/$(date +%Y-%m-%d).md

# Preview the exact DB content that would be sent to the LLM
uv run python -m wsbreporter.reporter --dry-run

# Include external news reality-check context and run the editor pass
uv run python -m wsbreporter.pipeline --with-news --edit-pass --markdown-output site/markdown/$(date +%Y-%m-%d).md
```

### 2. Daily Automation
To automate the entire process (generate + push to GitHub for deployment), use the provided script:

```bash
./daily_update.sh
```

You can set this up as a cron job to run daily.

### 3. Update the Website
Generate the static HTML site from the markdown letters:

```bash
# Build the site locally (output to _site/)
uv run python site/generate_site.py
```

Render a single Markdown report as standalone HTML:

```bash
uv run python -m wsbreporter.html site/markdown/$(date +%Y-%m-%d).md --output report.html
```

The site is automatically built and deployed to GitHub Pages via GitHub Actions when you push to `main`.

### Key Options
-   `-p, --posts NUMBER`: Number of posts to fetch (default: 25)
-   `-s, --subreddit NAME`: Subreddit to fetch from (default: wallstreetbets)
-   `--sort TYPE`: `hot`, `new`, `top`, `rising` (default: hot)
-   `--html`: Save as standalone HTML file (timestamped)
-   `-mo, --markdown-output FILE`: Save as markdown (required for site generation)
-   `--dry-run`: Print the LLM input without making an LLM call
-   `--with-news`: Fetch cached Google News RSS context for top tickers/themes
-   `--edit-pass`: Run a second LLM pass to polish and check source grounding

## Project Structure
-   `site/markdown/`: Source markdown letters.
-   `_site/`: Generated static website (ignored by git).
-   `config.py`: Configuration interface (reads from `.env`).
