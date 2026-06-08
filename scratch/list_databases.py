import os
import requests
import json
from dotenv import load_dotenv

load_dotenv(".env.local")
token = os.environ.get("NOTION_API_KEY")

headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28"
}

url = "https://api.notion.com/v1/search"
payload = {
    "filter": {
        "value": "database",
        "property": "object"
    }
}

res = requests.post(url, json=payload, headers=headers)
print(f"Status: {res.status_code}")
if res.status_code == 200:
    results = res.json().get("results", [])
    print(f"Found {len(results)} databases")
    for db in results:
        db_id = db["id"]
        title_list = db.get("title", [])
        title = title_list[0].get("plain_text", "Untitled") if title_list else "Untitled"
        props = list(db.get("properties", {}).keys())
        print(f"Title: {title} | ID: {db_id}")
        print(f"  Properties: {', '.join(props)}")
else:
    print(res.text)
