import os
import requests
from dotenv import load_dotenv

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(project_root, ".env.local"))

NOTION_API_KEY = os.getenv("NOTION_API_KEY")
DATABASE_ID = "36cddb45-8772-80c3-ab74-eb061ecee73f"

NOTION_HEADERS = {
    "Authorization": f"Bearer {NOTION_API_KEY}",
    "Notion-Version": "2022-06-28",
    "Content-Type": "application/json"
}

def list_unprocessed():
    url = f"https://api.notion.com/v1/databases/{DATABASE_ID}/query"
    payload = {
        "filter": {
            "property": "Status",
            "status": {
                "equals": "未処理"
            }
        }
    }
    res = requests.post(url, headers=NOTION_HEADERS, json=payload)
    if res.status_code == 200:
        pages = res.json().get("results", [])
        print(f"Found {len(pages)} unprocessed pages:")
        for idx, p in enumerate(pages, 1):
            title_prop = p["properties"].get("Name", {}).get("title") or []
            title = title_prop[0].get("plain_text") if title_prop else "Untitled"
            print(f"  {idx}. {title} (ID: {p['id']})")
    else:
        print(f"Failed: {res.text}")

if __name__ == "__main__":
    list_unprocessed()
