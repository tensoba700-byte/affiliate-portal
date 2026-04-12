import requests
import os
import json
import time
from publish_article import run_publish, NOTION_API_KEY, DATABASE_ID, headers

def get_completed_articles():
    url = f"https://api.notion.com/v1/databases/{DATABASE_ID}/query"
    query = {
        "filter": {
            "property": "ステータス 1",
            "select": { "equals": "完了" }
        }
    }
    res = requests.post(url, headers=headers, json=query)
    if res.status_code != 200:
        print(f"Error fetching completed items: {res.status_code}")
        return {}
    
    results = res.json().get("results", [])
    articles = {}
    for item in results:
        props = item.get("properties", {})
        title_list = props.get("記事タイトル", {}).get("rich_text", [])
        if not title_list: continue
        title = title_list[0]["plain_text"]
        cat = props.get("カテゴリ", {}).get("select", {}).get("name", "ガジェット")
        if title not in articles:
            articles[title] = {"category": cat, "items": []}
        articles[title]["items"].append(item["id"])
    
    return articles

def update_status(page_id, new_status):
    url = f"https://api.notion.com/v1/pages/{page_id}"
    payload = {
        "properties": {
            "ステータス 1": { "select": { "name": new_status } }
        }
    }
    requests.patch(url, headers=headers, json=payload)

def main():
    print("🔍 Checking for completed articles in Notion...")
    articles = get_completed_articles()
    
    if not articles:
        print("✅ No articles with '完了' status found.")
        return

    print(f"📝 Found {len(articles)} articles ready to publish.")
    
    for title, info in articles.items():
        success = run_publish(title, info["category"])
        if success:
            print(f"🎉 Successfully published: {title}")
            # Uncomment below if you want to update status automatically
            # for item_id in info["items"]:
            #     update_status(item_id, "公開済み") # Note: Ensure this status exists in Notion
        else:
            print(f"❌ Failed to publish: {title}")

if __name__ == "__main__":
    main()
