#!/bin/bash

# Configuration
TARGET_TIME="07:30"
PROJECT_DIR="/Users/tsukika/Desktop/affiliate-portal"
PYTHON_BIN="/Users/tsukika/.gemini/antigravity/scratch/discord-bot/venv/bin/python3"
SCRIPT_PATH="$PROJECT_DIR/scripts/morning_suggestion_discord.py"
LOG_FILE="$PROJECT_DIR/morning_automation.log"

echo "$(date): Morning suggestion service started. Target time: $TARGET_TIME daily." >> "$LOG_FILE"

while true; do
    CURRENT_TIME=$(date +"%H:%M")
    
    if [ "$CURRENT_TIME" == "$TARGET_TIME" ]; then
        echo "$(date): Triggering morning suggestion report..." >> "$LOG_FILE"
        $PYTHON_BIN $SCRIPT_PATH >> "$LOG_FILE" 2>&1
        # Sleep for a minute to avoid double triggering
        sleep 65
    fi
    
    # Check every 30 seconds
    sleep 30
done
