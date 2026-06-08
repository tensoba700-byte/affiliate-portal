import os
import requests
import json
from dotenv import load_dotenv

load_dotenv(".env.local")
token = os.environ.get("NOTION_API_KEY")
db_id = "36cddb45-8772-80c3-ab74-eb061ecee73f"  # みっけ！競合記事キュー

headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28"
}

url = f"https://api.notion.com/v1/databases/{db_id}/query"
payload = {
    "page_size": 100
}

res = requests.post(url, json=payload, headers=headers)
print(f"Status: {res.status_code}")
if res.status_code == 200:
    results = res.json().get("results", [])
    print(f"Found {len(results)} pages in queue:")
    for page in results:
        page_id = page["id"]
        props = page.get("properties", {})
        name = ""
        title_prop = props.get("Name", {}).get("title", [])
        if title_prop:
            name = title_prop[0].get("plain_text", "")
        status = props.get("Status", {}).get("select", {}).get("name", "なし")
        url_val = props.get("URL", {}).get("url", "なし")
        print(f"ID: {page_id} | Name: {name} | Status: {status} | URL: {url_val}")
else:
    print(res.text)
