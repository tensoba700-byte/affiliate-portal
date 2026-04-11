import requests
import os
import json
import random
import subprocess
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

# ----- Category Theme System -----
CATEGORY_THEMES = {
    '美容・スキンケア': {'bg1': '#3D0030', 'bg2': '#B84070', 'accent': '#FFD77A', 'pattern': 'stripes'},
    'ガジェット':       {'bg1': '#080E1F', 'bg2': '#1A3A70', 'accent': '#FFE600', 'pattern': 'dots'},
    'インテリア':       {'bg1': '#0D2B18', 'bg2': '#235C38', 'accent': '#FFFFFF', 'pattern': 'dots'},
    '生活雑貨':         {'bg1': '#4A1800', 'bg2': '#BD5000', 'accent': '#FFFFFF', 'pattern': 'diagonal'},
    '便利グッズ':       {'bg1': '#002030', 'bg2': '#005F85', 'accent': '#FFFFFF', 'pattern': 'dots'},
}

EYECATCH_PATTERNS = {
    'dots':     ('radial-gradient(circle, rgba(255,255,255,0.13) 1.5px, transparent 1.5px)', '18px 18px'),
    'stripes':  ('repeating-linear-gradient(45deg, rgba(255,255,255,0.07) 0, rgba(255,255,255,0.07) 2px, transparent 2px, transparent 16px)', 'auto'),
    'diagonal': ('repeating-linear-gradient(-45deg, rgba(255,255,255,0.06) 0, rgba(255,255,255,0.06) 3px, transparent 3px, transparent 22px)', 'auto'),
}


def extract_badge(title: str) -> str:
    """Derive a short badge text from the article title."""
    m = re.search(r'(\d+)選', title)
    if m:
        return f"人気{m.group(1)}選"
    if '比較' in title:
        return '徹底比較'
    if 'ランキング' in title:
        return '人気ランキング'
    if 'おすすめ' in title:
        return 'おすすめ特集'
    return 'みっけ！厳選'


def get_seasonal_catch_copy(category: str) -> str:
    """Generate a seasonal, category-aware catch copy."""
    month = datetime.datetime.now().month
    year = datetime.datetime.now().year
    if   3 <= month <= 5:  season = "春"
    elif 6 <= month <= 8:  season = "夏"
    elif 9 <= month <= 11: season = "秋"
    else:                  season = "冬"

    options = {
        'ガジェット': [
            f"{year}年{season}・テレワーカー必見の神アイテム",
            f"仕事効率を劇的に上げる{season}のデスク設備",
            f"{season}のデスク環境を本気で整える",
            f"2026年最新版・プロの使う{season}のガジェット",
        ],
        '美容・スキンケア': [
            f"{year}年{season}のベストコスメ山筋",
            f"{season}のルーティンをアップグレード",
            f"肀が剑的に変わる{season}のケアアイテム",
        ],
        'インテリア': [
            f"{year}年{season}・おしゃれな空間づくり",
            f"{season}のお部屋を素敵に模様替え",
        ],
        '生活雑貨': [
            f"{year}年{season}・毎日が快適になるモノ選び",
            f"{season}の新生活をもっと豊かに",
        ],
        '便利グッズ': [
            f"{year}年{season}・知らないと損する便利アイテム",
            f"暮らしをラクにする{season}のギア",
        ],
    }
    choices = options.get(category, [f"{year}年{season}のベストバイイテム"])
    return random.choice(choices)


def generate_eyecatch_html(slug: str, title: str, category: str, image_urls: list, catch_copy: str) -> str:
    """Generate a polished eyecatch with pattern overlay, text-stroke, and badge."""
    theme = CATEGORY_THEMES.get(category, CATEGORY_THEMES['ガジェット'])
    bg1, bg2, accent = theme['bg1'], theme['bg2'], theme['accent']
    pattern_css, pattern_size = EYECATCH_PATTERNS[theme['pattern']]
    badge = extract_badge(title)
    display_title = title if len(title) <= 30 else title[:29] + '…'
    accent_bar = accent if accent != '#FFFFFF' else 'rgba(255,255,255,0.35)'

    imgs = ""
    for url in image_urls[:5]:
        imgs += f'      <div class="pw"><img src="{url}" class="pi" alt="" /></div>\n'

    css = (
        "@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@700;900&display=swap');"
        "* { margin: 0; padding: 0; box-sizing: border-box; }"
        "html, body { width: 390px; height: 260px; overflow: hidden; }"
        "body { font-family: 'Noto Sans JP', 'Hiragino Kaku Gothic ProN', sans-serif; }"
        ".c { width: 390px; height: 260px; display: flex; flex-direction: column; }"
        f".t {{ background: linear-gradient(145deg, {bg1} 0%, {bg2} 100%); height: 170px; display:flex; flex-direction:column; justify-content:flex-end; padding:14px 22px 12px; position:relative; overflow:hidden; }}"
        f".pat {{ position:absolute; inset:0; background-image:{pattern_css}; background-size:{pattern_size}; pointer-events:none; }}"
        ".d1 { position:absolute; top:-45px; right:-35px; width:140px; height:140px; background:rgba(255,255,255,0.05); border-radius:50%; }"
        ".d2 { position:absolute; bottom:-30px; left:-25px; width:90px; height:90px; background:rgba(255,255,255,0.04); border-radius:50%; }"
        f".ab {{ position:absolute; top:0; left:0; right:0; height:5px; background:{accent_bar}; }}"
        ".ct { position:relative; z-index:2; }"
        ".br { display:flex; align-items:center; gap:8px; margin-bottom:5px; }"
        ".bn { font-size:9px; font-weight:900; color:rgba(255,255,255,0.55); letter-spacing:3px; text-transform:uppercase; }"
        ".bg { display:inline-block; background:#FFE600; color:#111; font-weight:900; font-size:10px; padding:2px 8px; border-radius:4px; letter-spacing:0.5px; }"
        ".ca { font-size:10px; font-weight:700; color:rgba(255,255,255,0.80); margin-bottom:5px; letter-spacing:0.3px; }"
        ".ti { font-size:15px; font-weight:900; color:#FFFFFF; line-height:1.42; -webkit-text-stroke:0.6px rgba(0,0,0,0.5); text-shadow:0 2px 10px rgba(0,0,0,0.75); display:-webkit-box; -webkit-line-clamp:2; -webkit-box-orient:vertical; overflow:hidden; }"
        f".b {{ background:#FFFFFF; flex:1; display:flex; align-items:center; justify-content:center; gap:10px; padding:8px 18px; position:relative; }}"
        f".b::before {{ content:''; position:absolute; top:0; left:0; right:0; height:3px; background:linear-gradient(90deg,{bg2},{bg1}); }}"
        ".pw { width:78px; height:78px; flex-shrink:0; display:flex; align-items:center; justify-content:center; }"
        ".pi { max-width:76px; max-height:76px; object-fit:contain; mix-blend-mode:multiply; }"
    )

    html = f"""<!DOCTYPE html>
<html lang="ja"><head><meta charset="UTF-8" /><style>{css}</style></head><body>
  <div class="c">
    <div class="t">
      <div class="pat"></div><div class="d1"></div><div class="d2"></div><div class="ab"></div>
      <div class="ct">
        <div class="br"><span class="bn">MIKKE!</span><span class="bg">{badge}</span></div>
        <p class="ca">{catch_copy}</p>
        <h1 class="ti">{display_title}</h1>
      </div>
    </div>
    <div class="b">
{imgs}    </div>
  </div>
</body></html>"""

    html_path = f"/Users/tsukika/Desktop/affiliate-portal/public/eyecatch/{slug}.html"
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f"  ✉️  Eyecatch HTML saved: {html_path}")
    return html_path


def take_eyecatch_screenshot(slug: str) -> bool:
    """Call the Node.js Puppeteer script to screenshot the HTML."""
    node_bin = "/Users/tsukika/.nvm/versions/node/v24.14.1/bin/node"
    script = "/Users/tsukika/Desktop/affiliate-portal/scripts/generate-eyecatch.js"
    try:
        result = subprocess.run(
            [node_bin, script, slug],
            capture_output=True, text=True, timeout=60,
            cwd="/Users/tsukika/Desktop/affiliate-portal"
        )
        print(result.stdout.strip())
        if result.returncode != 0:
            print(f"  ⚠️  Puppeteer error: {result.stderr[:200]}")
            return False
        return True
    except Exception as e:
        print(f"  ⚠️  Screenshot failed: {e}")
        return False


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
2. 商品紹介文（description）は各商品500文字以上で書いてください。
   ◎ 必ず含めること：
   - その商品を使う前と後の違いを具体的に（「コードが絡まらなくなった」「首の疲れが明らかに減った」など実感ベースで）
   - 他の商品と比べた時の具体的な違い（「同価格帯の製品よりノイズキャンセリングが段違い」など）
   - どんな人・シーンにぴったりか（「集中作業が多いフリーランス」「立ち仕事が多い方」など）
   ✕ 絶対に使わない言葉：「劇的に」「神機能」「1年後の生活が〜」「まさに」「なんと」「驚くほど」
   ✓ 代わりに使う：「実際に使ってみると〜」「口コミでも〜という声が多い」「〜のため〜できる」
   スマホで読みやすいよう2〜3文ごとに改行（\\nで表現）を入れてください。
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
      "description": "500文字以上の詳細紹介（改行\\nあり）",
      "score": 4.7,
      "pros": ["具体的メリット1（30文字以内）", "具体的メリット2", "具体的メリット3"],
      "cons": ["具体的デメリット1（30文字以内）", "具体的デメリット2"],
      "recommended_for": "こんな人におすすめ（30文字以内・例: テレワーク中心のビジネスパーソン）"
    }}
  ],
  "summary": "まとめ文（1000文字以上・絵文字を積極使用・各商品に「こんな方に最適」1行・最後は1位がおすすめ！で締める）"
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
        "max_tokens": 8000,
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

## ✅ 選び方のポイント
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

        # おすすめ対象をボタンの下に追加
        recommended_for_text = p_info.get('recommended_for', '')
        if recommended_for_text:
            markdown += f"\n\U0001f464 **こんな人におすすめ**: {recommended_for_text}\n\n"

    markdown += f"## \U0001f4ac まとめ\n{data['summary']}\n"

    # Write to fixed file path (overwrite the canonical article)
    file_path = f"/Users/tsukika/Desktop/affiliate-portal/src/content/articles/{FIXED_SLUG}.md"
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(markdown)

    print(f"\n✅ Published: {file_path}")

    # ----- Eyecatch image generation -----
    print("\n🎨 Generating eyecatch...")
    image_urls = [p['image_url'] for p in products if p.get('image_url')]
    catch_copy = get_seasonal_catch_copy(CATEGORY)
    generate_eyecatch_html(FIXED_SLUG, OUTPUT_ARTICLE_TITLE, CATEGORY, image_urls, catch_copy)
    ok = take_eyecatch_screenshot(FIXED_SLUG)
    if ok:
        print("📸 Eyecatch PNG generated successfully!")
    else:
        print("⚠️  Eyecatch PNG generation failed (article published without image).")

    return FIXED_SLUG


if __name__ == "__main__":
    publish()
