import requests
import os
import json
import argparse
import sys
from dotenv import load_dotenv

# Import the core publish function
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from publish_article import run_publish

def main():
    parser = argparse.ArgumentParser(description="Auto-publish articles from Notion based on schedule.")
    parser.add_argument("--time", choices=["morning", "night"], required=True, help="Processing window (morning=7am, night=8pm)")
    args = parser.parse_args()

    load_dotenv(".env.local")
    NOTION_API_KEY = os.getenv("NOTION_API_KEY")
    DATABASE_ID = os.getenv("NOTION_DATABASE_ID") or "8511908442c74738b78dc62f6a7a49d9"

    if not NOTION_API_KEY:
        print("Error: NOTION_API_KEY not found.")
        sys.exit(1)

    headers = {
        "Authorization": f"Bearer {NOTION_API_KEY}",
        "Notion-Version": "2022-06-28",
        "Content-Type": "application/json"
    }

    # Map argument to Notion property value
    target_time_value = "朝" if args.time == "morning" else "夜"

    # Query Notion for 1 article matching criteria
    payload = {
        "filter": {
            "and": [
                {
                    "property": "ステータス 1",
                    "select": {"equals": "完了"}
                },
                {
                    "property": "公開時間",
                    "select": {"equals": target_time_value}
                }
            ]
        },
        "page_size": 1
    }

    print(f"🔍 Searching for matching article ({target_time_value})...")
    res = requests.post(f"https://api.notion.com/v1/databases/{DATABASE_ID}/query", headers=headers, json=payload)
    if res.status_code != 200:
        print(f"Error querying Notion: {res.status_code} {res.text}")
        sys.exit(1)

    data = res.json()
    results = data.get("results", [])

    if not results:
        print(f"ℹ️ No articles found for timing: {target_time_value}")
        return

    page = results[0]
    page_id = page["id"]
    props = page["properties"]

    # Extract info
    title_parts = props.get("記事タイトル", {}).get("rich_text", [])
    article_title = title_parts[0]["plain_text"] if title_parts else "Untitled"
    category = props.get("カテゴリ", {}).get("select", {}).get("name", "その他")

    # Generate a slug
    import datetime
    date_str = datetime.datetime.now().strftime("%Y%m%d")
    slug_base = article_title.replace(" ", "-").lower()[:20]
    slug = f"{date_str}-{slug_base}"

    print(f"🚀 Found! Title: {article_title} (Category: {category})")
    print(f"✨ Generating article with Gemini 2.0 Flash...")

    # Execute publication
    success = run_publish(article_title, category, slug)

    if success:
        print(f"✅ Article generated and pushed successfully: {slug}")
        # Update Notion status to "投稿済み"
        update_payload = {
            "properties": {
                "ステータス 1": {"select": {"name": "投稿済み"}}
            }
        }
        u_res = requests.patch(f"https://api.notion.com/v1/pages/{page_id}", headers=headers, json=update_payload)
        if u_res.status_code == 200:
            print("📝 Notion status updated to '投稿済み'.")
        else:
            print(f"⚠️ Failed to update Notion status: {u_res.status_code} {u_res.text}")
    else:
        print("❌ Article generation failed.")

if __name__ == "__main__":
    main()
