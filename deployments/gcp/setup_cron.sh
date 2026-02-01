#!/bin/bash
# Setup cron job for wsbreporter daily update at 7pm EST/EDT

set -e

REPO_DIR="$HOME/wsbreporter"

# Check if repository exists
if [ ! -d "$REPO_DIR" ]; then
    echo "Error: Repository not found at $REPO_DIR"
    exit 1
fi

# Create logs directory
mkdir -p "$REPO_DIR/logs"

# Set system timezone
sudo timedatectl set-timezone America/New_York

# Add cron job
(crontab -l 2>/dev/null | grep -v wsbreporter; echo "0 19 * * * cd $HOME/wsbreporter && ./daily_update.sh >> $HOME/wsbreporter/logs/cron.log 2>&1") | crontab -

echo "✅ Cron job installed: Daily update at 7pm EST/EDT"
echo "View logs: tail -f $REPO_DIR/logs/cron.log"

