import os
import requests
from dotenv import load_dotenv

load_dotenv('.env.local')

NOTION_API_KEY = os.getenv("NOTION_API_KEY")
PAGE_ID = "37dddb45-8772-8172-81ea-f04de250b9c7"

if not NOTION_API_KEY:
    print("Error: NOTION_API_KEY is not defined in .env.local")
    exit(1)

headers = {
    "Authorization": f"Bearer {NOTION_API_KEY}",
    "Notion-Version": "2022-06-28",
    "Content-Type": "application/json"
}

url = f"https://api.notion.com/v1/pages/{PAGE_ID}"
payload = {
    "properties": {
        "Status": {
            "status": {"name": "未処理"}
        }
    }
}

try:
    response = requests.patch(url, headers=headers, json=payload)
    if response.status_code == 200:
        print("Successfully updated Notion status to '未処理'!")
    else:
        print(f"Error: Status {response.status_code}")
        print(response.text)
except Exception as e:
    print(f"Exception: {e}")
