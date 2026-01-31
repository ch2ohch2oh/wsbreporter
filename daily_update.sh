#!/bin/bash

# Navigate to the script's directory
cd "$(dirname "$0")"

# Pull latest changes
echo "Pulling latest changes..."
git pull

# Create venv if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

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
    git push
    
    echo "Done! The site will be built and deployed by GitHub Actions shortly."
else
    echo "Error: Failed to generate letter."
    exit 1
fi
