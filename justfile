set dotenv-load

today := `date +%Y-%m-%d`

default:
    just --list

scrape *args:
    UV_CACHE_DIR=.uv-cache uv run python -m wsbreporter.scraper {{args}}

report *args:
    UV_CACHE_DIR=.uv-cache uv run python -m wsbreporter.reporter --markdown-output site/markdown/{{today}}.md {{args}}

daily *args:
    UV_CACHE_DIR=.uv-cache uv run python -m wsbreporter.pipeline --markdown-output site/markdown/{{today}}.md {{args}}

site *args:
    UV_CACHE_DIR=.uv-cache uv run python site/generate_site.py {{args}}

help:
    UV_CACHE_DIR=.uv-cache uv run python -m wsbreporter.pipeline --help
