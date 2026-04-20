import requests
import os
import json
import sys
import datetime
import re
from dotenv import load_dotenv

# Import the core publish function
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from publish_article import run_publish

def slugify_title(title: str) -> str:
    """Generate a date-prefixed slug from an article title."""
    date_str = datetime.datetime.now().strftime("%Y%m%d")
    slug_base = re.sub(r'[^\w\s-]', '', title).strip().lower()
    slug_base = re.sub(r'[-\s]+', '-', slug_base)[:25]
    return f"{date_str}-{slug_base}"

def main():
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

    # 「完了」ステータスの記事を最古順で1件取得
    payload = {
        "filter": {
            "property": "ステータス 1",
            "select": {"equals": "完了"}
        },
        "sorts": [
            {
                "timestamp": "created_time",
                "direction": "ascending"
            }
        ],
        "page_size": 1
    }

    print("🔍 Searching for oldest article with status '完了'...")
    res = requests.post(
        f"https://api.notion.com/v1/databases/{DATABASE_ID}/query",
        headers=headers,
        json=payload
    )
    if res.status_code != 200:
        print(f"Error querying Notion: {res.status_code} {res.text}")
        sys.exit(1)

    results = res.json().get("results", [])

    if not results:
        print("ℹ️  No articles found with status '完了'. Nothing to publish.")
        return

    page = results[0]
    page_id = page["id"]
    props = page["properties"]

    # タイトル取得（rich_text または title プロパティ両対応）
    title_prop = props.get("記事タイトル", {})
    if title_prop.get("rich_text"):
        article_title = title_prop["rich_text"][0]["plain_text"]
    elif title_prop.get("title"):
        article_title = title_prop["title"][0]["plain_text"]
    else:
        article_title = "Untitled"

    category = props.get("カテゴリ", {}).get("select", {}).get("name", "ガジェット")
    slug = slugify_title(article_title)

    print(f"🚀 Found! Title: {article_title} (Category: {category})")
    print(f"✨ Generating article with Gemini...")

    # 記事生成・Markdownファイル保存・アイキャッチ画像生成
    success = run_publish(article_title, category, slug)

    if success:
        print(f"✅ Article generated successfully: {slug}")
        # Notionのステータスを「投稿済み」に更新
        update_payload = {
            "properties": {
                "ステータス 1": {"select": {"name": "投稿済み"}}
            }
        }
        u_res = requests.patch(
            f"https://api.notion.com/v1/pages/{page_id}",
            headers=headers,
            json=update_payload
        )
        if u_res.status_code == 200:
            print("📝 Notion status updated to '投稿済み'.")
        else:
            print(f"⚠️  Failed to update Notion status: {u_res.status_code} {u_res.text}")
    else:
        print("❌ Article generation failed.")
        sys.exit(1)

if __name__ == "__main__":
    main()
