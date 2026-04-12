import requests
import os
import json
import random
import subprocess
import datetime
import urllib.parse
import re
from dotenv import load_dotenv

# Load env from local directory
load_dotenv("/Users/tsukika/Desktop/affiliate-portal/.env.local")
load_dotenv("/Users/tsukika/.gemini/antigravity/scratch/discord-bot/.env")

NOTION_API_KEY = os.getenv("NOTION_API_KEY")
DATABASE_ID = os.getenv("NOTION_DATABASE_ID")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

headers = {
    "Authorization": f"Bearer {NOTION_API_KEY}",
    "Notion-Version": "2022-06-28",
    "Content-Type": "application/json"
}

# ----- Category Theme System -----
CATEGORY_THEMES = {
    '美容・スキンケア': {'bg1': '#3D0030', 'bg2': '#B84070', 'accent': '#FFD77A', 'pattern': 'stripes'},
    'ガジェット':       {'bg1': '#080E1F', 'bg2': '#1A3A70', 'accent': '#FFE600', 'pattern': 'dots'},
    'ガジェット・家電': {'bg1': '#080E1F', 'bg2': '#1A3A70', 'accent': '#FFE600', 'pattern': 'dots'},
    'インテリア':       {'bg1': '#0D2B18', 'bg2': '#235C38', 'accent': '#FFFFFF', 'pattern': 'dots'},
    '生活雑貨':         {'bg1': '#4A1800', 'bg2': '#BD5000', 'accent': '#FFFFFF', 'pattern': 'diagonal'},
    '便利グッズ':       {'bg1': '#002030', 'bg2': '#005F85', 'accent': '#FFFFFF', 'pattern': 'dots'},
}

EYECATCH_PATTERNS = {
    'dots':     ('radial-gradient(circle, rgba(255,255,255,0.13) 1.5px, transparent 1.5px)', '18px 18px'),
    'stripes':  ('repeating-linear-gradient(45deg, rgba(255,255,255,0.07) 0, rgba(255,255,255,0.07) 2px, transparent 2px, transparent 16px)', 'auto'),
    'diagonal': ('repeating-linear-gradient(-45deg, rgba(255,255,255,0.06) 0, rgba(255,255,255,0.06) 3px, transparent 3px, transparent 22px)', 'auto'),
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
    theme = CATEGORY_THEMES.get(category, CATEGORY_THEMES['ガジェット'])
    bg1, bg2, accent = theme['bg1'], theme['bg2'], theme['accent']
    pattern_css, pattern_size = EYECATCH_PATTERNS[theme['pattern']]
    badge = extract_badge(title)
    display_title = title if len(title) <= 30 else title[:29] + '…'
    accent_bar = accent if accent != '#FFFFFF' else 'rgba(255,255,255,0.35)'
    imgs = "".join([f'<div class="pw"><img src="{url}" class="pi" alt="" /></div>\n' for url in image_urls[:5]])
    css = f"""@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@700;900&display=swap');
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
html, body {{ width: 390px; height: 260px; overflow: hidden; }}
body {{ font-family: 'Noto Sans JP', sans-serif; }}
.c {{ width: 390px; height: 260px; display: flex; flex-direction: column; }}
.t {{ background: linear-gradient(145deg, {bg1} 0%, {bg2} 100%); height: 170px; display:flex; flex-direction:column; justify-content:flex-end; padding:14px 22px 12px; position:relative; overflow:hidden; }}
.pat {{ position:absolute; inset:0; background-image:{pattern_css}; background-size:{pattern_size}; pointer-events:none; }}
.d1 {{ position:absolute; top:-45px; right:-35px; width:140px; height:140px; background:rgba(255,255,255,0.05); border-radius:50%; }}
.d2 {{ position:absolute; bottom:-30px; left:-25px; width:90px; height:90px; background:rgba(255,255,255,0.04); border-radius:50%; }}
.ab {{ position:absolute; top:0; left:0; right:0; height:5px; background:{accent_bar}; }}
.ct {{ position:relative; z-index:2; }}
.br {{ display:flex; align-items:center; gap:8px; margin-bottom:5px; }}
.bn {{ font-size:9px; font-weight:900; color:rgba(255,255,255,0.55); letter-spacing:3px; text-transform:uppercase; }}
.bg {{ display:inline-block; background:#FFE600; color:#111; font-weight:900; font-size:10px; padding:2px 8px; border-radius:4px; letter-spacing:0.5px; }}
.ca {{ font-size:10px; font-weight:700; color:rgba(255,255,255,0.80); margin-bottom:5px; letter-spacing:0.3px; }}
.ti {{ font-size:15px; font-weight:900; color:#FFFFFF; line-height:1.42; -webkit-text-stroke:0.6px rgba(0,0,0,0.5); text-shadow:0 2px 10px rgba(0,0,0,0.75); display:-webkit-box; -webkit-line-clamp:2; -webkit-box-orient:vertical; overflow:hidden; }}
.b {{ background:#FFFFFF; flex:1; display:flex; align-items:center; justify-content:center; gap:10px; padding:8px 18px; position:relative; }}
.b::before {{ content:''; position:absolute; top:0; left:0; right:0; height:3px; background:linear-gradient(90deg,{bg2},{bg1}); }}
.pw {{ width:78px; height:78px; flex-shrink:0; display:flex; align-items:center; justify-content:center; }}
.pi {{ max-width:76px; max-height:76px; object-fit:contain; mix-blend-mode:multiply; }}"""
    html = f"""<!DOCTYPE html>
<html lang="ja"><head><meta charset="UTF-8" /><style>{css}</style></head><body>
<div class="c"><div class="t"><div class="pat"></div><div class="d1"></div><div class="d2"></div><div class="ab"></div>
<div class="ct"><div class="br"><span class="bn">MIKKE!</span><span class="bg">{badge}</span></div><p class="ca">{catch_copy}</p><h1 class="ti">{display_title}</h1></div></div>
<div class="b">{imgs}</div></div></body></html>"""
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
            "category": props.get("カテゴリ", {}).get("select", {}).get("name", "ガジェット")
        })
    return products

def generate_content_with_llm(products_data, article_title):
    llm_products = [{"name": p["name"]} for p in products_data]
    prompt = f"""あなたはプロの家電レビューライターです。2026年時点の設定で、以下の商品{len(llm_products)}点の比較レビュー記事をJSONで作成してください。
商品紹介は各500文字以上。URLや価格は含めない。
summaryは1000文字以上、絵文字多用。最後は1位がおすすめ！で締める。
{json.dumps(llm_products, ensure_ascii=False)}
出力形式: {{"excerpt": "...", "intro": "...", "points": ["...", "...", "..."], "products": [{{"name": "...", "description": "...", "score": 4.8, "pros": ["...", "...", "..."], "cons": ["...", "..."], "recommended_for": "..."}}], "summary": "..."}}"""
    res = requests.post("https://api.groq.com/openai/v1/chat/completions", headers={"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}, json={
        "model": "llama-3.3-70b-versatile",
        "messages": [{"role": "system", "content": "日本語のJSONのみ出力。"}, {"role": "user", "content": prompt}],
        "temperature": 0.6, "max_tokens": 8000, "response_format": {"type": "json_object"}
    })
    return res.json()["choices"][0]["message"]["content"] if res.status_code == 200 else None

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
    markdown = f"--- \ntitle: \"{output_title}\"\ncoverImage: \"\"\nexcerpt: \"{data['excerpt']}\"\npublishDate: \"{datetime.datetime.now().isoformat()}\"\ncategory: \"{category}\"\n---\n\n{data['intro']}\n\n## ✅ 選び方のポイント\n<ul>" + "".join([f"<li>{p}</li>" for p in data['points']]) + "</ul>\n\n"
    for i, p in enumerate(data['products']):
        rank = i + 1
        notion_p = next((x for x in products if x['name'].lower() in p['name'].lower() or p['name'].lower() in x['name'].lower()), None)
        markdown += f"### 👑 第{rank}位: {p['name']}\n"
        if notion_p and notion_p['image_url']: markdown += f"IMAGE: {notion_p['image_url']}\n"
        markdown += f"[総合評価: {p['score']}]\n\n"
        if notion_p:
            for platform in ['amazon', 'rakuten', 'yahoo']:
                price = notion_p.get(f'{platform}_price')
                if price: markdown += f"{platform.upper()}_PRICE: {price}\n"
            for platform, key in [('amazon', 'asin'), ('rakuten', 'rakuten'), ('yahoo', 'yahoo')]:
                url = notion_p.get(f'{platform}_url')
                if url: markdown += f"{key.upper()}: {url}\n"
        # Format description for markdown
        formatted_desc = p['description'].replace('\\n', '\n\n')
        markdown += f"\n{formatted_desc}\n\n[AMAZON_LINK_HERE] [RAKUTEN_LINK_HERE] [YAHOO_LINK_HERE]\n\n:::pro\n" + "\n".join([f"- {m}" for m in p['pros']]) + "\n:::\n:::con\n" + "\n".join([f"- {c}" for c in p['cons']]) + "\n:::\n\n👤 **こんな人におすすめ**: " + p.get('recommended_for', '') + "\n\n"
    markdown += f"## 💬 まとめ\n{data['summary']}\n"
    path = f"/Users/tsukika/Desktop/affiliate-portal/src/content/articles/{slug}.md"
    with open(path, 'w', encoding='utf-8') as f: f.write(markdown)
    image_urls = [p['image_url'] for p in products if p.get('image_url')]
    generate_eyecatch_html(slug, output_title, category, image_urls, get_seasonal_catch_copy(category))
    take_eyecatch_screenshot(slug)
    return True

if __name__ == "__main__":
    run_publish("【2024年春】テレワークが劇的に捗る！デスク周りのおすすめガジェット7選", "ガジェット", "20260411-telework-gadgets-f401")
