import requests
import os
import json
import datetime
import uuid
from dotenv import load_dotenv

# Load env from local directory
load_dotenv("/Users/tsukika/Desktop/affiliate-portal/.env.local")
# Load env from scratch bot directory for Groq API Key
load_dotenv("/Users/tsukika/.gemini/antigravity/scratch/discord-bot/.env")

NOTION_API_KEY = os.getenv("NOTION_API_KEY")
DATABASE_ID = os.getenv("NOTION_DATABASE_ID")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

headers = {
    "Authorization": f"Bearer {NOTION_API_KEY}",
    "Notion-Version": "2022-06-28",
    "Content-Type": "application/json"
}

# Notion query title (original)
ARTICLE_TITLE = "【2024年春】テレワークが劇的に捗る！デスク周りのおすすめガジェット7選"
# Output title (year corrected to 2026)
OUTPUT_ARTICLE_TITLE = "【2026年春】テレワークが劇的に捗る！デスク周りのおすすめガジェット7選"
CATEGORY = "ガジェット"

def get_notion_data():
    url = f"https://api.notion.com/v1/databases/{DATABASE_ID}/query"
    payload = {
        "filter": {
            "property": "記事タイトル",
            "rich_text": {"equals": ARTICLE_TITLE}
        }
    }
    response = requests.post(url, headers=headers, json=payload)
    if response.status_code == 200:
        results = response.json().get("results", [])
        products = []
        for result in results:
            props = result.get("properties", {})

            def get_rich_text(prop_name):
                rt = props.get(prop_name, {}).get("rich_text", [])
                return rt[0]["plain_text"] if rt else ""

            def get_url(prop_name):
                # Support both url-type and rich_text-type properties
                prop = props.get(prop_name, {})
                if prop.get("type") == "url":
                    return prop.get("url") or ""
                return get_rich_text(prop_name)

            # Prices are stored as rich_text like "¥12,990" - strip to numeric string
            def get_price(prop_name):
                raw = get_rich_text(prop_name)
                # Remove ¥ and commas to get pure number string
                return raw.replace("¥", "").replace(",", "").strip()

            p = {
                "name": props.get("商品名", {}).get("title", [{}])[0].get("text", {}).get("content", ""),
                "image_url": get_url("Image URL"),
                "amazon_url": get_url("Amazon Affiliate URL"),
                "rakuten_url": get_url("Rakuten Affiliate URL"),
                "yahoo_url": get_url("Yahoo Affiliate URL"),
                "amazon_price": get_price("Amazon Price"),
                "rakuten_price": get_price("Rakuten Price"),
                "yahoo_price": get_price("Yahoo Price"),
            }
            products.append(p)
        return products
    return []

def generate_content_with_llm(products_data):
    """Call Groq to generate the descriptions for each product"""
    prompt = f"""
あなたはプロの家電・ライフスタイルライター（愛称：おこげ社長）です。
以下の商品リストをもとに、読者の心に刺さる最高の比較・紹介記事を作成してください。

【執筆ルール】
1. 年号は必ず「2026年」を使用してください。
2. 商品紹介文は1つあたり150文字〜200文字程度で、具体的かつ詳細に書いてください。
3. メリット・デメリットは「安い」「便利」といった当たり前のことではなく、
   「〇〇なシーンで特に役立つ」「従来のモデルと比べて〇〇が改善されている」など、
   実際に使った人しか分からないような深い洞察や、読者が「なるほど」と思う視点を含めてください。
4. 説明文の中にURLや価格は絶対に含めないでください。

【商品リスト】
{json.dumps(products_data, ensure_ascii=False, indent=2)}

【出力形式】
以下の構造のJSONで出力してください：
{{
  "excerpt": "記事のリード文（50文字程度）",
  "intro": "導入文（読者の共感を得る内容）",
  "points": ["選び方のポイント1", "選び方のポイント2", "選び方のポイント3"],
  "products": [
    {{
      "name": "商品名",
      "description": "具体的で詳細な紹介文（150文字以上）",
      "score": 4.5,
      "pros": ["実用的なメリット1", "実用的なメリット2"],
      "cons": ["許容できるデメリット1", "注意すべきデメリット1"]
    }}
  ],
  "summary": "まとめ文（読者の背中を押す言葉）"
}}
"""
    
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": [
            {"role": "system", "content": "あなたは最高のライターです。必ず日本語で、指定されたJSON形式のみを返してください。"},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7,
        "response_format": {"type": "json_object"}
    }
    
    res = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=payload)
    if res.status_code == 200:
        return res.json()["choices"][0]["message"]["content"]
    return None

def publish():
    print(f"Fetching Notion data for '{ARTICLE_TITLE}'...")
    products = get_notion_data()
    if not products:
        print("No products found.")
        return

    print("Generating content with LLM...")
    raw_content = generate_content_with_llm(products)
    if not raw_content:
        print("LLM generation failed.")
        return
    
    data = json.loads(raw_content)
    
    # 5. Format Markdown
    markdown = f"""---
title: "{OUTPUT_ARTICLE_TITLE}"
coverImage: ""
excerpt: "{data['excerpt']}"
publishDate: "{datetime.datetime.now().isoformat()}"
category: "{CATEGORY}"
---

{data['intro']}

## 選び方のポイント
<ul>
{" ".join([f"<li>{p}</li>" for p in data['points']])}
</ul>

"""

    print(f"Debug: LLM returned {len(data['products'])} products")
    
    for i, p_info in enumerate(data['products']):
        rank = i + 1
        # Robust matching: check if LLM name is in Notion names or vice versa
        notion_p = next((x for x in products if x['name'] in p_info['name'] or p_info['name'] in x['name']), None)
        
        if not notion_p:
            print(f"⚠️ Could not match product: {p_info['name']}")
        
        markdown += f"### 👑 第{rank}位: {p_info['name']}\n"
        if notion_p and notion_p['image_url']:
            print(f"DEBUG: Found IMAGE for {p_info['name']}: {notion_p['image_url']}")
            markdown += f"IMAGE: {notion_p['image_url']}\n"
        
        markdown += f"[総合評価: {p_info['score']}]\n\n"
        
        if notion_p:
            # Prices are already plain numeric strings e.g. "12990"
            if notion_p['amazon_price']: markdown += f"AMAZON_PRICE: {notion_p['amazon_price']}\n"
            if notion_p['rakuten_price']: markdown += f"RAKUTEN_PRICE: {notion_p['rakuten_price']}\n"
            if notion_p['yahoo_price']: markdown += f"YAHOO_PRICE: {notion_p['yahoo_price']}\n"
            
            # Use specific affiliate URLs if provided by Qclaw
            if notion_p['amazon_url']: markdown += f"ASIN: {notion_p['amazon_url']}\n"
            if notion_p['rakuten_url']: markdown += f"RAKUTEN: {notion_p['rakuten_url']}\n"
            if notion_p['yahoo_url']: markdown += f"YAHOO: {notion_p['yahoo_url']}\n"

        markdown += f"{p_info['description']}\n\n"
        
        markdown += ":::pro\n" + "\n".join([f"- {m}" for m in p_info['pros']]) + "\n:::\n"
        markdown += ":::con\n" + "\n".join([f"- {c}" for c in p_info['cons']]) + "\n:::\n\n"
        
        markdown += "[AMAZON_LINK_HERE] [RAKUTEN_LINK_HERE] [YAHOO_LINK_HERE]\n\n"

    markdown += f"## まとめ\n{data['summary']}\n"

    # Write to file
    slug = f"20260411-telework-gadgets-{uuid.uuid4().hex[:4]}"
    file_path = f"/Users/tsukika/Desktop/affiliate-portal/src/content/articles/{slug}.md"
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(markdown)
    
    print(f"✅ Published: {file_path}")
    return slug

if __name__ == "__main__":
    publish()
