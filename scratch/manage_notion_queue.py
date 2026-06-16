#!/usr/bin/env python3
import os
import sys
import requests
from dotenv import load_dotenv

def main():
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    load_dotenv(os.path.join(project_root, ".env.local"))

    NOTION_API_KEY = os.getenv("NOTION_API_KEY")
    DATABASE_ID = "36cddb45-8772-80c3-ab74-eb061ecee73f"  # 「みっけ！競合記事キュー」のID

    if not NOTION_API_KEY:
        print("❌ Error: NOTION_API_KEY is not set in .env.local")
        sys.exit(1)

    headers = {
        "Authorization": f"Bearer {NOTION_API_KEY}",
        "Notion-Version": "2022-06-28",
        "Content-Type": "application/json"
    }

    # 1. 現在の「未処理」レコードを取得する
    print("🔄 Fetching unprocessed items from Notion...")
    query_url = f"https://api.notion.com/v1/databases/{DATABASE_ID}/query"
    payload = {
        "filter": {
            "property": "Status",
            "status": {
                "equals": "未処理"
            }
        }
    }
    
    res = requests.post(query_url, headers=headers, json=payload, timeout=10)
    if res.status_code != 200:
        print(f"❌ Failed to fetch unprocessed items: {res.status_code} {res.text}")
        sys.exit(1)

    results = res.json().get("results", [])
    print(f"Found {len(results)} unprocessed items.")

    # 2. 既存の「未処理」レコードのステータスを「保留」または「完了」に変更して避難させる
    for idx, page in enumerate(results, 1):
        page_id = page["id"]
        props = page["properties"]
        title_prop = props.get("Name", {}).get("title") or []
        name_str = title_prop[0].get("plain_text") if title_prop else "Untitled"
        print(f"[{idx}/{len(results)}] Deferring: {name_str} (ID: {page_id})")

        # 「完了」または別のステータスに変更。Statusは「status」タイププロパティ。
        update_payload = {
            "properties": {
                "Status": {
                    "status": {
                        "name": "完了"  # パイプラインが処理しないように「完了」に変更して避難
                    }
                }
            }
        }
        res_patch = requests.patch(f"https://api.notion.com/v1/pages/{page_id}", headers=headers, json=update_payload, timeout=10)
        if res_patch.status_code == 200:
            print(f"  ✅ Successfully deferred {name_str}")
        else:
            print(f"  ❌ Failed to defer {name_str}: {res_patch.status_code} {res_patch.text}")

    # 3. マスカラおすすめ人気ランキングを追加する
    print("\n🔄 Adding new target: マスカラのおすすめ人気ランキング (https://my-best.com/392)")
    add_payload = {
        "parent": { "database_id": DATABASE_ID },
        "properties": {
            "Name": {
                "title": [
                    { "text": { "content": "マスカラのおすすめ人気ランキング" } }
                ]
            },
            "URL": {
                "url": "https://my-best.com/392"
            },
            "Category": {
                "select": {
                    "name": "美容・スキンケア"
                }
            },
            "Status": {
                "status": {
                    "name": "未処理"
                }
            }
        }
    }

    res_post = requests.post("https://api.notion.com/v1/pages", headers=headers, json=add_payload, timeout=10)
    if res_post.status_code == 200:
        print("🎉 Target successfully added as '未処理'!")
    else:
        print(f"❌ Failed to add target: {res_post.status_code} {res_post.text}")
        sys.exit(1)

if __name__ == "__main__":
    main()
