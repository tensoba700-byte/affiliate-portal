#!/bin/bash
DIR="$(cd "$(dirname "$0")" && pwd)"
PYTHON_PATH="/Users/tsukika/.gemini/antigravity/scratch/discord-bot/venv/bin/python3"
LOG="$DIR/taro-bot.log"
exec "$PYTHON_PATH" -u "$DIR/taro-discord-bot.py" >> "$LOG" 2>&1
