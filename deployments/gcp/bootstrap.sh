#!/bin/bash
# Bootstrap script for GCP Compute Engine instance
# This script installs all dependencies needed to run wsbreporter

set -e

echo "=== WSB Reporter - GCP Compute Engine Bootstrap ==="
echo ""

# Update system packages
echo "Updating system packages..."
sudo apt-get update
sudo apt-get upgrade -y

# Install system dependencies
echo "Installing system dependencies..."
sudo apt-get install -y curl git

# Install uv
echo "Installing uv..."
curl -LsSf https://astral.sh/uv/install.sh | sh
export PATH="$HOME/.local/bin:$PATH"

# Install Python dependencies
echo "Syncing Python dependencies..."
uv sync --frozen

# Set up environment variables
echo ""
echo "=== Environment Configuration ==="
echo "Please create a .env file with your API credentials:"
echo "  cd $REPO_DIR"
echo "  nano .env"
echo ""
echo "Required variables:"
echo "  REDDIT_CLIENT_ID=your_client_id"
echo "  REDDIT_CLIENT_SECRET=your_client_secret"
echo "  REDDIT_USER_AGENT=your_user_agent"
echo "  LLM_PROVIDER=gemini"
echo "  GEMINI_API_KEY=your_gemini_key"
echo ""
echo "Optional alternatives:"
echo "  LLM_PROVIDER=deepseek"
echo "  DEEPSEEK_API_KEY=your_deepseek_key"
echo "  DEEPSEEK_MODEL_NAME=deepseek-chat"
echo ""

# Configure git
echo "Configuring git..."
git config --global user.email "bot@wsbreporter.com"
git config --global user.name "WSB Reporter Bot"

echo ""
echo "=== Bootstrap Complete ==="
echo "Next steps:"
echo "1. Create .env file with your API credentials"
echo "2. Configure GitHub authentication (SSH key or token)"
echo "3. Run ./setup_cron.sh to set up the daily job"
echo ""
