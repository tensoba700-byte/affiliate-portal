#!/bin/bash
# Move to project directory
cd /Users/tsukika/Desktop/affiliate-portal

# Load virtual environment
source /Users/tsukika/.gemini/antigravity/scratch/discord-bot/venv/bin/activate

# 1. Generate articles from Notion
echo "--- Running Auto Publish Batch ---"
python3 scripts/auto_publish_batch.py

# 2. Build for production (ensures content is picked up and no errors)
echo "--- Building Next.js Site ---"
npm run build

# 3. GitHub Push
echo "--- Pushing to GitHub ---"
git add .
git commit -m "chore: automated article publication $(date +'%Y-%m-%d %H:%M:%S')"
git push origin main

echo "--- Automation Complete ---"
