import requests
import os
import json
import datetime
import urllib.parse
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
# Fixed slug - always overwrites the canonical article file
FIXED_SLUG = "20260411-telework-gadgets-f401"


def get_notion_data():
    url = f"https://api.notion.com/v1/databases/{DATABASE_ID}/query"
    payload = {
        "filter": {
            "property": "記事タイトル",
            "rich_text": {"equals": ARTICLE_TITLE}
        }
    }
    response = requests.post(url, headers=headers, json=payload)
    if response.status_code != 200:
        print(f"Notion API error: {response.status_code}")
        return []

    results = response.json().get("results", [])
    products = []

    for result in results:
        props = result.get("properties", {})

        def get_rich_text(prop_name):
            rt = props.get(prop_name, {}).get("rich_text", [])
            return rt[0]["plain_text"] if rt else ""

        def get_url_prop(prop_name):
            prop = props.get(prop_name, {})
            if prop.get("type") == "url":
                return prop.get("url") or ""
            return get_rich_text(prop_name)

        def get_price(prop_name):
            raw = get_rich_text(prop_name)
            return raw.replace("¥", "").replace(",", "").strip()

        def decode_rakuten_url(url: str) -> str:
            """Ensure the pc= parameter in Rakuten affiliate URLs is NOT URL-encoded."""
            if not url:
                return url
            # Decode all percent-encoded characters so pc=https%3A%2F%2F... becomes pc=https://...
            return urllib.parse.unquote(url)

        amazon_url = get_url_prop("Amazon Affiliate URL")
        rakuten_url = decode_rakuten_url(get_url_prop("Rakuten Affiliate URL"))
        yahoo_url = get_url_prop("Yahoo Affiliate URL")

        p = {
            "name": props.get("商品名", {}).get("title", [{}])[0].get("text", {}).get("content", ""),
            "image_url": get_url_prop("Image URL"),
            "amazon_url": amazon_url,
            "rakuten_url": rakuten_url,
            "yahoo_url": yahoo_url,
            "amazon_price": get_price("Amazon Price"),
            "rakuten_price": get_price("Rakuten Price"),
            "yahoo_price": get_price("Yahoo Price"),
        }
        products.append(p)

    return products


def generate_content_with_llm(products_data):
    """Call Groq to generate high-quality article content for each product."""
    # Only pass product names to LLM - URLs and prices come from Notion
    llm_products = [{"name": p["name"]} for p in products_data]

    prompt = f"""
あなたはプロの家電・ガジェットレビューライター（愛称：おこげ社長）です。
以下の商品7点について、読者が「絶対欲しい！今すぐ買う！」と思うような最高の比較レビュー記事を日本語で作成してください。

【執筆ルール】
1. 年号は必ず「2026年」を使用してください。
2. 商品紹介文（description）は、読者の購買意欲を最高潮に高めるために「各商品500文字以上」で徹底的に詳しく執筆してください。
   以下を必ず深掘りして含めること：
   - 導入：読者が今抱えている悩み（肩こり、集中力の欠如、デスクの乱れ等）への共感
   - 使用感：届いた瞬間のワクワク感、設置した時のデスクの見違え具合
   - 具体的な機能美：他社製品にはない、この製品だけの「神機能」の解説
   - 結論：これを使うことで、あなたの1年後の生活がどう「劇的に」良くなるか（生産性の向上、疲れにくさ等）
   スマホユーザーが飽きないよう、2〜3文ごとに適切な位置で改行（\\nで表現）を入れてください。
3. スコア（score）は実際の市場評価・口コミ実績を忠実に反映した数値：
   - 4.9〜5.0: 業界最高峰・他を圧倒する（例: HHKB）
   - 4.7〜4.8: 非常に高品質・プロ愛用（例: Sony WH-1000XM5）
   - 4.4〜4.6: 高品質・多くのユーザーに支持
   - 4.0〜4.3: 良品・特定用途向け
4. pros（メリット）は3つ、cons（デメリット）は2つ。
   - 「高品質」「便利」「コスパが良い」「高価」などの抽象的・当たり前の言葉は絶対に禁止！
   - 「高価」という言葉は絶対に使わないでください。代わりに「初期投資はかかるが長期コスパは良い」など具体的に。
   - 「〇〇なシーンで△△の問題を解決できる」など具体的な状況で書く
   - 各項目は35文字以内でコンパクトに
5. URLや価格は絶対に含めないこと。

【商品リスト】
{json.dumps(llm_products, ensure_ascii=False, indent=2)}

【出力形式（JSON のみ出力）】
{{
  "excerpt": "記事のリード文（60文字程度）",
  "intro": "導入文（テレワーカーの課題感から入る・100〜150文字、改行あり）",
  "points": ["具体的な選び方ポイント1", "具体的な選び方ポイント2", "具体的な選び方ポイント3"],
  "products": [
    {{
      "name": "商品名（入力と同じ表記）",
      "description": "200文字以上の詳細紹介（改行\\nあり）",
      "score": 4.7,
      "pros": ["具体的メリット1（30文字以内）", "具体的メリット2", "具体的メリット3"],
      "cons": ["具体的デメリット1（30文字以内）", "具体的デメリット2"]
    }}
  ],
  "summary": "まとめ文（購買意欲を後押しする・80文字程度）"
}}
"""

    llm_headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": [
            {"role": "system", "content": "あなたは最高のガジェットレビューライターです。必ず日本語で、指定されたJSON形式のみを返してください。URLや価格は絶対に含めないでください。"},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.65,
        "max_tokens": 4000,
        "response_format": {"type": "json_object"}
    }

    res = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=llm_headers, json=payload)
    if res.status_code == 200:
        return res.json()["choices"][0]["message"]["content"]
    print(f"LLM error: {res.status_code} {res.text}")
    return None


def publish():
    print(f"Fetching Notion data for '{ARTICLE_TITLE}'...")
    products = get_notion_data()
    if not products:
        print("No products found.")
        return

    print(f"Found {len(products)} products from Notion.")
    for p in products:
        amazon_preview = p['amazon_url'][:70] if p['amazon_url'] else 'NONE'
        rakuten_preview = p['rakuten_url'][:70] if p['rakuten_url'] else 'NONE'
        print(f"  - {p['name']}")
        print(f"    amazon : {amazon_preview}")
        print(f"    rakuten: {rakuten_preview}")

    print("\nGenerating content with LLM...")
    raw_content = generate_content_with_llm(products)
    if not raw_content:
        print("LLM generation failed.")
        return

    data = json.loads(raw_content)

    # Build Markdown
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

    print(f"LLM returned {len(data['products'])} products")

    for i, p_info in enumerate(data['products']):
        rank = i + 1
        # Match LLM product name to Notion product (case-insensitive substring match)
        notion_p = next(
            (x for x in products
             if x['name'].lower() in p_info['name'].lower()
             or p_info['name'].lower() in x['name'].lower()),
            None
        )

        if not notion_p:
            print(f"  ⚠️ Could not match: '{p_info['name']}'")

        markdown += f"### 👑 第{rank}位: {p_info['name']}\n"

        if notion_p and notion_p['image_url']:
            markdown += f"IMAGE: {notion_p['image_url']}\n"
            print(f"  [{rank}] IMAGE OK: {notion_p['image_url'][:60]}")

        markdown += f"[総合評価: {p_info['score']}]\n\n"

        if notion_p:
            # Prices (plain numeric strings)
            if notion_p['amazon_price']:
                markdown += f"AMAZON_PRICE: {notion_p['amazon_price']}\n"
            if notion_p['rakuten_price']:
                markdown += f"RAKUTEN_PRICE: {notion_p['rakuten_price']}\n"
            if notion_p['yahoo_price']:
                markdown += f"YAHOO_PRICE: {notion_p['yahoo_price']}\n"

            # Affiliate URLs - written exactly as retrieved from Notion, NO modification
            if notion_p['amazon_url']:
                markdown += f"ASIN: {notion_p['amazon_url']}\n"
                print(f"  [{rank}] AMAZON: {notion_p['amazon_url']}")
            if notion_p['rakuten_url']:
                markdown += f"RAKUTEN: {notion_p['rakuten_url']}\n"
                print(f"  [{rank}] RAKUTEN: {notion_p['rakuten_url'][:80]}")
            if notion_p['yahoo_url']:
                markdown += f"YAHOO: {notion_p['yahoo_url']}\n"

        # Description with mobile-friendly line breaks
        description = p_info['description'].replace('\\n', '\n\n')
        markdown += f"\n{description}\n\n"

        # Pros/Cons compact — buttons come BEFORE pros/cons
        pros = p_info.get('pros', [])[:3]
        cons = p_info.get('cons', [])[:2]

        # Buttons FIRST (above pros/cons)
        markdown += "[AMAZON_LINK_HERE] [RAKUTEN_LINK_HERE] [YAHOO_LINK_HERE]\n\n"

        markdown += ":::pro\n" + "\n".join([f"- {m}" for m in pros]) + "\n:::\n"
        markdown += ":::con\n" + "\n".join([f"- {c}" for c in cons]) + "\n:::\n\n"

    markdown += f"## まとめ\n{data['summary']}\n"

    # Write to fixed file path (overwrite the canonical article)
    file_path = f"/Users/tsukika/Desktop/affiliate-portal/src/content/articles/{FIXED_SLUG}.md"
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(markdown)

    print(f"\n✅ Published: {file_path}")
    return FIXED_SLUG


if __name__ == "__main__":
    publish()
