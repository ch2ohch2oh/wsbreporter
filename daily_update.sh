#!/bin/bash

# Navigate to the script's directory
cd "$(dirname "$0")"

# Source .env if it exists
if [ -f .env ]; then
    source .env
fi

# Pull latest changes
echo "Pulling latest changes..."
if [ -n "$GITHUB_TOKEN" ]; then
    git pull "https://$GITHUB_TOKEN@github.com/ch2ohch2oh/wsbreporter.git" main
else
    git pull
fi

# Create venv if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Get today's date
TODAY=$(date +%Y-%m-%d)
FILENAME="site/markdown/${TODAY}.md"

echo "Generating letter for $TODAY..."

# Generate the letter
python run.py --markdown-output "$FILENAME"

# Check if generation was successful
if [ -f "$FILENAME" ]; then
    echo "Letter generated successfully: $FILENAME"
    
    # Git operations
    echo "Pushing to GitHub..."
    git add "$FILENAME"
    git commit -m "Auto-generate letter for $TODAY"
    
    if [ -n "$GITHUB_TOKEN" ]; then
        git push "https://$GITHUB_TOKEN@github.com/ch2ohch2oh/wsbreporter.git" main
    else
        git push
    fi
    
    echo "Done! The site will be built and deployed by GitHub Actions shortly."
else
    echo "Error: Failed to generate letter."
    exit 1
fi
