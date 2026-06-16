import os
import requests
from dotenv import load_dotenv

# Load env
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

try:
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        data = response.json()
        print("Success!")
        properties = data.get("properties", {})
        
        # Print important property values
        for prop_name, prop_val in properties.items():
            ptype = prop_val.get("type")
            val = None
            if ptype == "title":
                title_list = prop_val.get("title", [])
                val = "".join([t.get("text", {}).get("content", "") for t in title_list])
            elif ptype == "rich_text":
                text_list = prop_val.get("rich_text", [])
                val = "".join([t.get("text", {}).get("content", "") for t in text_list])
            elif ptype == "select":
                val = prop_val.get("select", {}).get("name") if prop_val.get("select") else None
            elif ptype == "url":
                val = prop_val.get("url")
            else:
                val = prop_val
            print(f"- {prop_name}: {val}")
    else:
        print(f"Error: Status {response.status_code}")
        print(response.text)
except Exception as e:
    print(f"Exception: {e}")
