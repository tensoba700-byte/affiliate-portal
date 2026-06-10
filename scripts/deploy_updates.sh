#!/bin/bash
# Move to project directory
cd /Users/tsukika/Desktop/affiliate-portal

# Load virtual environment
source /Users/tsukika/.gemini/antigravity/scratch/discord-bot/venv/bin/activate

# 1. Generate articles from Notion
echo "--- Running Auto Publish Batch ---"
python3 scripts/auto_publish_batch.py

# 1.5. Update internal links
echo "--- Updating Internal Links ---"
python3 scripts/add_internal_links.py

# 2. Build for production (ensures content is picked up and no errors)
echo "--- Building Next.js Site ---"
npm run build

# 3. GitHub Push
echo "--- Pushing to GitHub ---"
git add .
git commit -m "chore: automated article publication $(date +'%Y-%m-%d %H:%M:%S')"
git push origin main

# 4. Wait for Vercel deployment (150s) and trigger Google Indexing API
echo "--- Waiting for Vercel deployment to finish (150s) ---"
sleep 150
echo "--- Triggering Google Indexing API ---"
python3 scripts/seo_automation.py

echo "--- Automation Complete ---"
