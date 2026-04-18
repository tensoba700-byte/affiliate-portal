import requests
import os
import json
import random
import subprocess
import datetime
import urllib.parse
import re
import google.generativeai as genai
from dotenv import load_dotenv

# Load env from local directory
load_dotenv("/Users/tsukika/Desktop/affiliate-portal/.env.local")
load_dotenv("/Users/tsukika/.gemini/antigravity/scratch/discord-bot/.env")

NOTION_API_KEY = os.getenv("NOTION_API_KEY")
DATABASE_ID = os.getenv("NOTION_DATABASE_ID")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

headers = {
    "Authorization": f"Bearer {NOTION_API_KEY}",
    "Notion-Version": "2022-06-28",
    "Content-Type": "application/json"
}

ARTICLE_SCHEMA = {
    "type": "object",
    "properties": {
        "excerpt": {"type": "string"},
        "intro": {"type": "string"},
        "points": {
            "type": "array",
            "items": {"type": "string"}
        },
        "products": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "description": {"type": "string"},
                    "recommended_for": {
                        "type": "array",
                        "items": {"type": "string"}
                    }
                },
                "required": ["name", "description", "recommended_for"]
            }
        },
        "summary": {"type": "string"}
    },
    "required": ["excerpt", "intro", "points", "products", "summary"]
}

# ----- Category Theme System -----
CATEGORY_THEMES = {
    '美容・スキンケア': {'bg1': '#FF9EDB', 'bg2': '#FF69B4', 'accent': '#FFFFFF', 'pattern': 'water'},
    'ガジェット':       {'bg1': '#00F2FF', 'bg2': '#0066FF', 'accent': '#FFFFFF', 'pattern': 'digital'},
    'ガジェット・家電': {'bg1': '#00F2FF', 'bg2': '#0066FF', 'accent': '#FFFFFF', 'pattern': 'digital'},
    'インテリア':       {'bg1': '#98FF98', 'bg2': '#2E8B57', 'accent': '#FFFFFF', 'pattern': 'natural'},
    '生活雑貨':         {'bg1': '#FFD700', 'bg2': '#FF8C00', 'accent': '#FFFFFF', 'pattern': 'diagonal'},
    '便利グッズ':       {'bg1': '#FFA07A', 'bg2': '#FF4500', 'accent': '#FFFFFF', 'pattern': 'dots'},
}

EYECATCH_PATTERNS = {
    'dots':     ('radial-gradient(circle, rgba(255,255,255,0.2) 2px, transparent 2px)', '20px 20px'),
    'water':    ('radial-gradient(circle at 20% 30%, rgba(255,255,255,0.4) 0%, transparent 40%)', 'auto'),
    'digital':  ('linear-gradient(rgba(255,255,255,0.1) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.1) 1px, transparent 1px)', '25px 25px'),
    'natural':  ('radial-gradient(circle, rgba(255,255,255,0.15) 3px, transparent 3px)', '24px 24px'),
}

def slugify(text: str) -> str:
    """Generate a filename-friendly slug from title."""
    text = text.replace("2024", "2026")
    text = re.sub(r'[^\w\s-]', '', text).strip().lower()
    text = re.sub(r'[-\s]+', '-', text)
    date_prefix = datetime.datetime.now().strftime("%Y%m%d")
    return f"{date_prefix}-{text[:30]}"

def extract_badge(title: str) -> str:
    m = re.search(r'(\d+)選', title)
    if m: return f"人気{m.group(1)}選"
    if '比較' in title: return '徹底比較'
    if 'ランキング' in title: return '人気ランキング'
    if 'おすすめ' in title: return 'おすすめ特集'
    return 'みっけ！厳選'

def get_seasonal_catch_copy(category: str) -> str:
    month = datetime.datetime.now().month
    year = datetime.datetime.now().year
    season = "春" if 3 <= month <= 5 else "夏" if 6 <= month <= 8 else "秋" if 9 <= month <= 11 else "冬"
    options = {
        'ガジェット': [f"{year}年{season}・テレワーカー必見の神アイテム", f"仕事効率を劇的に上げる{season}のデスク設備"],
        'ガジェット・家電': [f"{year}年{season}・テレワーカー必見の神アイテム", f"仕事効率を劇的に上げる{season}のデスク設備"],
        '美容・スキンケア': [f"{year}年{season}のベストコスメ山筋", f"{season}のルーティンをアップグレード"],
        'インテリア': [f"{year}年{season}・おしゃれな空間づくり", f"{season}のお部屋を素敵に模様替え"],
        '生活雑貨': [f"{year}年{season}・毎日が快適になるモノ選び", f"{season}の新生活をもっと豊かに"],
        '便利グッズ': [f"{year}年{season}・知らないと損する便利アイテム", f"暮らしをラクにする{season}のギア"],
    }
    choices = options.get(category, [f"{year}年{season}のベストバイアイテム"])
    return random.choice(choices)

def generate_eyecatch_html(slug: str, title: str, category: str, image_urls: list, catch_copy: str) -> str:
    display_title = title if len(title) <= 30 else title[:29] + '…'
    
    # 1200x630 simple white grid design
    imgs_html = ""
    target_count = min(6, len(image_urls))
    for url in image_urls[:target_count]:
        imgs_html += f'<div class="pw"><img src="{url}" class="pi" alt="" /></div>\n'
    
    css = f"""@import url('https://fonts.googleapis.com/css2?family=M+PLUS+Rounded+1c:wght@800;900&display=swap');
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
html, body {{ width: 1200px; height: 630px; overflow: hidden; background: #fff; }}
body {{ font-family: 'M PLUS Rounded 1c', sans-serif; display: flex; flex-direction: column; align-items: center; justify-content: center; position: relative; }}
.g {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 40px; width: 1000px; padding: 40px; }}
.pw {{ width: 280px; height: 280px; display: flex; align-items: center; justify-content: center; }}
.pi {{ max-width: 260px; max-height: 260px; object-fit: contain; mix-blend-mode: multiply; }}
.to {{ position: absolute; inset: 0; display: flex; flex-direction: column; align-items: center; justify-content: center; z-index: 10; pointer-events: none; }}
.tb {{ background: rgba(255, 255, 255, 0.65); padding: 40px 80px; text-align: center; box-shadow: 0 0 0 78px rgba(255, 255, 255, 0.65); }}
.ti {{ font-size: 64px; font-weight: 900; color: #000; line-height: 1.2; letter-spacing: -2px; }}
"""
    html = f"""<!DOCTYPE html>
<html lang="ja"><head><meta charset="UTF-8" /><style>{css}</style></head><body>
<div class="g">{imgs_html}</div>
<div class="to"><div class="tb"><h1 class="ti">{display_title}</h1></div></div>
</body></html>"""
    path = f"/Users/tsukika/Desktop/affiliate-portal/public/eyecatch/{slug}.html"
    with open(path, 'w', encoding='utf-8') as f: f.write(html)
    return path
    path = f"/Users/tsukika/Desktop/affiliate-portal/public/eyecatch/{slug}.html"
    with open(path, 'w', encoding='utf-8') as f: f.write(html)
    return path

def take_eyecatch_screenshot(slug: str) -> bool:
    node_bin = "/Users/tsukika/.nvm/versions/node/v24.14.1/bin/node"
    script = "/Users/tsukika/Desktop/affiliate-portal/scripts/generate-eyecatch.js"
    try:
        subprocess.run([node_bin, script, slug], capture_output=True, text=True, timeout=60, cwd="/Users/tsukika/Desktop/affiliate-portal")
        return True
    except: return False

def get_notion_data(article_title: str):
    url = f"https://api.notion.com/v1/databases/{DATABASE_ID}/query"
    payload = {"filter": {"property": "記事タイトル", "rich_text": {"equals": article_title}}}
    res = requests.post(url, headers=headers, json=payload)
    if res.status_code != 200: return []
    results = res.json().get("results", [])
    products = []
    for r in results:
        props = r.get("properties", {})
        def get_rt(name):
            rt = props.get(name, {}).get("rich_text", [])
            return rt[0]["plain_text"] if rt else ""
        def get_url(name):
            p = props.get(name, {})
            return p.get("url") or get_rt(name)
        def get_price(name):
            return get_rt(name).replace("¥", "").replace(",", "").strip()
        cat_prop = props.get("カテゴリ", {})
        cat_select = cat_prop.get("select") if cat_prop else None
        products.append({
            "id": r.get("id"),
            "name": props.get("商品名", {}).get("title", [{}])[0].get("text", {}).get("content", ""),
            "image_url": get_url("Image URL"),
            "amazon_url": get_url("Amazon Affiliate URL"),
            "rakuten_url": urllib.parse.unquote(get_url("Rakuten Affiliate URL") or ""),
            "yahoo_url": get_url("Yahoo Affiliate URL"),
            "amazon_price": get_price("Amazon Price"),
            "rakuten_price": get_price("Rakuten Price"),
            "yahoo_price": get_price("Yahoo Price"),
            "category": cat_select.get("name", "ガジェット") if cat_select else "ガジェット"
        })
    return products

def generate_content_with_llm(products_data, article_title):
    llm_products = [{"name": p["name"]} for p in products_data]
    prompt = f"""あなたはプロのWebライターとして、中立的かつ信頼性の高い商品紹介記事を執筆してください。
読者に親しみやすさを感じさせつつも、過度な装飾やAI特有の極端な表現を避けた、誠実なトーンを維持してください。

【厳守事項】
1. **ランキング形式の禁止**: 全ての商品を「おすすめの選択肢」として並列に扱ってください。順位や「第○位」という表現は一切使わないでください。
2. **NGワード**: 「マジで」「ヤバい」「神アイテム」「最高」「究極」などの煽り文句や、過剰な強調表現は使用禁止です。
3. **一人称の禁止**: 「おこげ」「私」といった一人称や個人の体験談を装った記述は全て削除してください。
4. **商品説明の制限**: 各商品の紹介（description）は、**500文字以内**で簡潔にまとめてください。
5. **絵文字の活用**: 各見出しおよび商品説明の各文章に、内容に沿った適切な絵文字を配置してください。
6. **ターゲット層**: 各商品に対し、「こんな人におすすめ！」という項目で、具体的な推奨理由を**3つの箇条書き**で作成してください。

2026年時点の最新トレンドを踏まえ、以下の商品{len(llm_products)}点のおすすめ紹介記事をJSONで作成してください。
URLや価格は含めないでください。

{json.dumps(llm_products, ensure_ascii=False)}

出力形式: {{"excerpt": "...", "intro": "...", "points": ["...", "...", "..."], "products": [{{"name": "...", "description": "...", "recommended_for": ["...", "...", "..."]}}], "summary": "..."}}"""
    
    model = genai.GenerativeModel('gemini-2.0-flash')
    res = model.generate_content(
        prompt,
        generation_config=genai.types.GenerationConfig(
            temperature=0.6,
            max_output_tokens=8192,
            response_mime_type="application/json",
            response_schema=ARTICLE_SCHEMA
        )
    )
    return res.text if res else None

def run_publish(article_title: str, category: str = None, slug: str = None):
    print(f"🚀 Processing: {article_title}")
    products = get_notion_data(article_title)
    if not products: return False
    category = category or products[0].get("category", "ガジェット")
    output_title = article_title.replace("2024", "2026")
    slug = slug or slugify(article_title)
    raw = generate_content_with_llm(products, output_title)
    if not raw: return False
    data = json.loads(raw)
    markdown = f"--- \ntitle: \"{output_title}\"\ncoverImage: \"\"\nexcerpt: \"{data['excerpt']}\"\npublishDate: \"{datetime.datetime.now().isoformat()}\"\ncategory: \"{category}\"\n---\n\n> [!NOTE]\n> 本記事はアフィリエイト広告を利用しています\n\n{data['intro']}\n\n## ✅ 選び方のポイント\n<ul>" + "".join([f"<li>{p}</li>" for p in data['points']]) + "</ul>\n\n"
    for i, p in enumerate(data['products']):
        notion_p = next((x for x in products if x['name'].lower() in p['name'].lower() or p['name'].lower() in x['name'].lower()), None)
        # 順位バッジや「第○位」を削除し、絵文字付きの並列見出しに変更
        markdown += f"### 🌸 {p['name']}\n"
        if notion_p and notion_p['image_url']: markdown += f"IMAGE: {notion_p['image_url']}\n"
        
        if notion_p:
            for platform in ['amazon', 'rakuten', 'yahoo']:
                price = notion_p.get(f'{platform}_price')
                if price: markdown += f"{platform.upper()}_PRICE: {price}\n"
            for platform, key in [('amazon', 'asin'), ('rakuten', 'rakuten'), ('yahoo', 'yahoo')]:
                url = notion_p.get(f'{platform}_url')
                if url: markdown += f"{key.upper()}: {url}\n"
        
        # 説明文のフォーマット（500文字以内）
        formatted_desc = p['description'].replace('\\n', '\n\n')
        markdown += f"\n{formatted_desc}\n\n[AMAZON_LINK_HERE] [RAKUTEN_LINK_HERE] [YAHOO_LINK_HERE]\n\n"
        
        # 「こんな人におすすめ！」箇条書きの追加
        markdown += f"👤 **こんな人におすすめ！**\n"
        markdown += "\n".join([f"- {item}" for item in p['recommended_for']]) + "\n\n"
    markdown += f"## 💬 まとめ\n{data['summary']}\n"
    path = f"/Users/tsukika/Desktop/affiliate-portal/src/content/articles/{slug}.md"
    with open(path, 'w', encoding='utf-8') as f: f.write(markdown)
    image_urls = [p['image_url'] for p in products if p.get('image_url')]
    generate_eyecatch_html(slug, output_title, category, image_urls, get_seasonal_catch_copy(category))
    take_eyecatch_screenshot(slug)
    return True

if __name__ == "__main__":
    run_publish(
        "GW前に旅行グッズ・アウトドア用品をチェック！人気アイテムとおすすめの使い方", 
        "便利グッズ", 
        "20260415-gw-travel-outdoor"
    )
