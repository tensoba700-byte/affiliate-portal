import requests
import re

urls = [
    "https://my-best.com/3401",
    "https://my-best.com/1473",
    "https://my-best.com/33",
    "https://my-best.com/461",
    "https://my-best.com/2322",
    "https://my-best.com/7123",
    "https://my-best.com/2418",
    "https://my-best.com/2643",
    "https://my-best.com/2642",
    "https://my-best.com/2644"
]

headers = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
}

for url in urls:
    try:
        res = requests.get(url, headers=headers, timeout=5)
        m = re.search(r'<title[^>]*>(.*?)</title>', res.text, re.IGNORECASE | re.DOTALL)
        title = m.group(1).strip() if m else "No Title Found"
        # 不要な改行や空白を除去
        title = re.sub(r'\s+', ' ', title)
        print(f"{url} -> {title}")
    except Exception as e:
        print(f"{url} -> Error: {e}")
