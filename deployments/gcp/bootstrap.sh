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

# Install Python 3.11 and pip
echo "Installing Python 3.11..."
sudo apt-get install -y python3.11 python3.11-venv python3-pip git

# Create virtual environment
echo "Creating Python virtual environment..."
python3.11 -m venv venv

# Activate virtual environment and install dependencies
echo "Installing Python dependencies..."
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

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
echo "  GEMINI_API_KEY=your_gemini_key"
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
