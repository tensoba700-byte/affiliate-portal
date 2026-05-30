import os
import sys
import requests
from dotenv import load_dotenv

def main():
    ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    load_dotenv(os.path.join(ROOT_DIR, ".env.local"))

    NOTION_API_KEY = os.getenv("NOTION_API_KEY")
    DATABASE_ID = "36cddb45-8772-80c3-ab74-eb061ecee73f"

    if not NOTION_API_KEY:
        print("❌ Error: NOTION_API_KEY is not set in .env.local")
        sys.exit(1)

    headers = {
        "Authorization": f"Bearer {NOTION_API_KEY}",
        "Notion-Version": "2022-06-28",
        "Content-Type": "application/json"
    }

    payload = {
        "parent": { "database_id": DATABASE_ID },
        "properties": {
            "Name": {
                "title": [
                    {
                        "text": {
                            "content": "水草育成LEDライトのおすすめ人気ランキング"
                        }
                    }
                ]
            },
            "URL": {
                "url": "https://my-best.com/21509"
            },
            "Category": {
                "select": {
                    "name": "ガーデニング"
                }
            },
            "Status": {
                "status": {
                    "name": "未処理"
                }
            }
        }
    }

    print(f"🔄 Pushing target URL https://my-best.com/21509 to Notion...")
    try:
        res = requests.post("https://api.notion.com/v1/pages", headers=headers, json=payload, timeout=10)
        if res.status_code == 200:
            print("✅ Successfully added target URL to Notion database!")
        else:
            print(f"❌ Failed to add: Status {res.status_code}, Response: {res.text}")
    except Exception as e:
        print(f"❌ Error occurred: {e}")

if __name__ == "__main__":
    main()
