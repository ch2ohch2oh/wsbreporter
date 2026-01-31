# WSB Reporter

A tool to fetch and summarize Reddit posts from r/wallstreetbets using Gemini AI, and generate a static website of the letters.

## Setup

1.  **Install dependencies**:
    ```bash
    ./venv/bin/pip install -r requirements.txt
    ```

2.  **Configure API keys**:
    Copy the example environment file and fill in your Reddit and Gemini API credentials:
    ```bash
    cp .env.example .env
    # Edit .env with your keys
    ```

## Usage

### 1. Generate a Letter
Fetched posts are summarized into a markdown letter. You can save it directly to the site content directory:

```bash
# Generate today's letter
./start.sh --markdown-output site/markdown/$(date +%Y-%m-%d).md
```

### 2. Update the Website
Generate the static HTML site from the markdown letters:

```bash
# Build the site locally (output to _site/)
./venv/bin/python site/generate_site.py
```

The site is automatically built and deployed to GitHub Pages via GitHub Actions when you push to `main`.

### Key Options (`./start.sh` or `python run.py`)
-   `-p, --posts NUMBER`: Number of posts to fetch (default: 25)
-   `-s, --subreddit NAME`: Subreddit to fetch from (default: wallstreetbets)
-   `--sort TYPE`: `hot`, `new`, `top`, `rising` (default: hot)
-   `--html`: Save as standalone HTML file (timestamped)
-   `-mo, --markdown-output FILE`: Save as markdown (required for site generation)

## Project Structure
-   `site/markdown/`: Source markdown letters.
-   `_site/`: Generated static website (ignored by git).
-   `config.py`: Configuration interface (reads from `.env`).
