#!/usr/bin/env python3
import os
import sys
import requests
from dotenv import load_dotenv

def main():
    # Load env variables
    ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    load_dotenv(os.path.join(ROOT_DIR, ".env.local"))

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

    # List of 10 competitor URLs with unique categories
    items = [
        {
            "name": "クレンジングバームのおすすめ人気ランキング",
            "url": "https://my-best.com/13106",
            "category": "美容・スキンケア"
        },
        {
            "name": "化粧水のおすすめ人気ランキング",
            "url": "https://my-best.com/products/434",
            "category": "美容・スキンケア"
        },
        {
            "name": "さっぱり化粧水のおすすめ人気ランキング",
            "url": "https://my-best.com/products/8473",
            "category": "美容・スキンケア"
        },
        {
            "name": "クッションファンデのおすすめ人気ランキング",
            "url": "https://my-best.com/products/416624",
            "category": "美容・スキンケア"
        },
        {
            "name": "プチプラクッションファンデのおすすめ人気ランキング",
            "url": "https://my-best.com/products/416641",
            "category": "美容・スキンケア"
        },
        {
            "name": "美白美容液のおすすめ人気ランキング",
            "url": "https://my-best.com/products/847",
            "category": "美容・スキンケア"
        },
        {
            "name": "日焼け止めのおすすめ人気ランキング",
            "url": "https://my-best.com/products/439",
            "category": "美容・スキンケア"
        },
        {
            "name": "オーガニックのリップクリームのおすすめ人気ランキング",
            "url": "https://my-best.com/products/850",
            "category": "美容・スキンケア"
        },
        {
            "name": "かわいいリップクリームのおすすめ人気ランキング",
            "url": "https://my-best.com/products/851",
            "category": "美容・スキンケア"
        },
        {
            "name": "アイシャドウのおすすめ人気ランキング",
            "url": "https://my-best.com/products/680",
            "category": "美容・スキンケア"
        }
    ]

    print(f"🔄 Adding {len(items)} competitor URLs to Notion database {DATABASE_ID}...")
    success_count = 0

    for idx, item in enumerate(items, 1):
        payload = {
            "parent": { "database_id": DATABASE_ID },
            "properties": {
                "Name": {
                    "title": [
                        {
                            "text": {
                                "content": item["name"]
                            }
                        }
                    ]
                },
                "URL": {
                    "url": item["url"]
                },
                "Category": {
                    "select": {
                        "name": item["category"]
                    }
                },
                "Status": {
                    "status": {
                        "name": "未処理"
                    }
                }
            }
        }

        try:
            res = requests.post("https://api.notion.com/v1/pages", headers=headers, json=payload, timeout=10)
            if res.status_code == 200:
                print(f"   [{idx}/10] ✅ Successfully added: {item['name']} ({item['category']})")
                success_count += 1
            else:
                print(f"   [{idx}/10] ❌ Failed to add: {item['name']} -> Status: {res.status_code}, Response: {res.text}")
        except Exception as e:
            print(f"   [{idx}/10] ❌ Error occurred while adding {item['name']}: {e}")

    print("\n==========================================")
    print(f"🎉 Notion database updates completed!")
    print(f"   Success: {success_count}/{len(items)}")
    print("==========================================")

if __name__ == "__main__":
    main()
