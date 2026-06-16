import requests
import json
import re
from bs4 import BeautifulSoup

url = "https://my-best.com/25751"
headers = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
}
resp = requests.get(url, headers=headers, timeout=10)
if resp.status_code == 200:
    html = resp.text
    json_ld_blocks = re.findall(r'<script type="application/ld\+json">(.*?)</script>', html, re.DOTALL)
    for i, block in enumerate(json_ld_blocks):
        try:
            data = json.loads(block.strip())
            if isinstance(data, dict) and data.get("@type") == "Article":
                main_entity = data.get("mainEntity")
                item_lists = []
                if isinstance(main_entity, list):
                    item_lists = main_entity
                elif isinstance(main_entity, dict):
                    item_lists = [main_entity]
                
                for item in item_lists:
                    if isinstance(item, dict) and item.get("@type") == "ItemList":
                        list_items = item.get("itemListElement", [])
                        print(f"Found ItemList with {len(list_items)} items")
                        for li in list_items[:3]:
                            prod = li.get("item", {})
                            print(f"Product Name: {prod.get('name')}")
                            print(f"Keys: {list(prod.keys())}")
                            if "aggregateRating" in prod:
                                print(f"AggregateRating: {prod['aggregateRating']}")
                            else:
                                print("No aggregateRating key")
        except Exception as e:
            print(f"Error block {i}: {e}")
else:
    print(f"Failed to fetch: {resp.status_code}")
