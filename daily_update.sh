#!/bin/bash
set -e

cd "$(dirname "$0")"

if [ -f .env ]; then
    source .env
fi

echo "Pulling latest changes..."
if [ -n "$GITHUB_TOKEN" ]; then
    git pull "https://$GITHUB_TOKEN@github.com/ch2ohch2oh/wsbreporter.git" main
else
    git pull origin main
fi

echo "Syncing dependencies..."
uv sync --frozen

TODAY=$(date +%Y-%m-%d)
echo "Generating letter for $TODAY..."

just daily --edit-pass --with-news
just site

if [ -f "site/markdown/${TODAY}.md" ]; then
    echo "Pushing to GitHub..."
    git add site/markdown/"${TODAY}".md
    git commit -m "Auto-generate letter for $TODAY"
    if [ -n "$GITHUB_TOKEN" ]; then
        git push "https://$GITHUB_TOKEN@github.com/ch2ohch2oh/wsbreporter.git" main
    else
        git push origin main
    fi
    echo "Done."
else
    echo "Error: Letter not generated."
    exit 1
fi
