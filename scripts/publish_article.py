import requests
import os
import json
import random
import subprocess
import datetime
import urllib.parse
import re
import time
from dotenv import load_dotenv

# API統計用グローバル変数
g_api_call_count = 0
g_json_retry_count = 0

# Load env from local directory
load_dotenv(".env.local")
# For local bot development (optional/ignored if not found)
load_dotenv(os.path.expanduser("~/.gemini/antigravity/scratch/discord-bot/.env"))

NOTION_API_KEY = os.getenv("NOTION_API_KEY")
DATABASE_ID = os.getenv("NOTION_DATABASE_ID")

headers = {
    "Authorization": f"Bearer {NOTION_API_KEY}",
    "Notion-Version": "2022-06-28",
    "Content-Type": "application/json"
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

# --- 変数名パターン（記事から除去する） ---
VARIABLE_NAME_PATTERNS = [
    r'\b(YAHOO_PRICE|RAKUTEN_PRICE|AMAZON_PRICE)\b\s*[:：]?\s*\S*',
    r'\b(YAHOO|RAKUTEN|AMAZON|ASIN)\s*[:：]\s*\S*',
    r'\bYAHOO_PRICE\b',
    r'\bRAKUTEN_PRICE\b',
    r'\bAMAZON_PRICE\b',
]


def load_generation_rules() -> str:
    """GENERATION_RULES.md を読み込んでプロンプト用テキストとして返す。"""
    rules_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "GENERATION_RULES.md"
    )
    if os.path.exists(rules_path):
        with open(rules_path, 'r', encoding='utf-8') as f:
            return f.read()
    return ""


def clean_variable_names(text: str) -> str:
    """記事テキストから変数名（YAHOO_PRICE等）を除去する。"""
    for pattern in VARIABLE_NAME_PATTERNS:
        text = re.sub(pattern, '', text, flags=re.IGNORECASE)
    # 余分な空行をまとめる
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text


CATEGORY_SLUGS = {
    "美容液": "serum",
    "クレンジングオイル": "cleansing-oil",
    "化粧水": "toner",
    "フェイスパック": "face-mask",
    "シートマスク": "face-mask",
    "クレンジングバーム": "cleansing-balm",
    "アイライナー": "eyeliner",
    "シャンプー": "shampoo",
    "トリートメント": "treatment",
    "ヘアオイル": "hair-oil",
    "リップ": "lip",
    "ファンデーション": "foundation",
    "日焼け止め": "sunscreen",
    "コンシーラー": "concealer",
    "アイシャドウ": "eyeshadow",
    "マスカラ": "mascara",
    "チーク": "blush",
}

def slugify(text: str, category: str = None, publish_date: str = None) -> str:
    """Generate a filename-friendly slug from title."""
    slug_part = None
    for keyword, eng_slug in CATEGORY_SLUGS.items():
        if keyword in text:
            slug_part = eng_slug
            break
            
    date_prefix = None
    if publish_date:
        m = re.match(r'^(\d{4})-(\d{2})-(\d{2})', publish_date.strip())
        if m:
            date_prefix = f"{m.group(1)}{m.group(2)}{m.group(3)}"
            
    if not date_prefix:
        jst = datetime.timezone(datetime.timedelta(hours=9))
        date_prefix = datetime.datetime.now(jst).strftime("%Y%m%d")

    if slug_part:
        return f"{date_prefix}-{slug_part}"
    else:
        print(f"[WARN] Unknown category: {category or 'None'}")
        
        articles_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "src", "content", "articles"
        )
        os.makedirs(articles_dir, exist_ok=True)
        
        num = 1
        while True:
            candidate_slug = f"{date_prefix}-article-{num:03d}"
            file_path = os.path.join(articles_dir, f"{candidate_slug}.md")
            if not os.path.exists(file_path):
                return candidate_slug
            num += 1

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
        '美容・スキンケア': [f"{year}年{season}のベストコスメ特集", f"{season}のルーティンをアップグレード"],
        'インテリア': [f"{year}年{season}・おしゃれな空間づくり", f"{season}のお部屋を素敵に模様替え"],
        '生活雑貨': [f"{year}年{season}・毎日が快適になるモノ選び", f"{season}の新生活をもっと豊かに"],
        '便利グッズ': [f"{year}年{season}・知らないと損する便利アイテム", f"暮らしをラクにする{season}のギア"],
    }
    choices = options.get(category, [f"{year}年{season}のベストバイアイテム"])
    return random.choice(choices)

def format_eyecatch_title(title: str) -> str:
    """
    アイキャッチ用タイトルを3行に整形する。
    """
    import re
    m = re.match(r'^(.+?)。【(.+?)(\d+選)】$', title)
    if m:
        emotional   = m.group(1)
        description = m.group(2)
        count_part  = m.group(3)
        split_m = re.search(
            r'^(.*[\u3041-\u3096])([\u4e00-\u9fff\u30a0-\u30ff].+)$',
            description
        )
        if split_m:
            line2 = split_m.group(1)
            line3 = f'【{split_m.group(2)}{count_part}】'
        else:
            line2 = description
            line3 = f'【{count_part}】'
        return f'{emotional}<br />{line2}<br />{line3}'
    if len(title) <= 11:
        return title
    separators = ["の", "で", "に", "は", "が", "を", "！", "？", "：", "、", " ", "　"]
    mid = len(title) // 2
    for offset in [0, 1, -1, 2, -2, 3, -3]:
        idx = mid + offset
        if 0 < idx < len(title) - 1 and title[idx] in separators:
            return title[:idx+1] + "<br />" + title[idx+1:]
    return title[:mid] + "<br />" + title[mid:]

def generate_eyecatch_html(slug: str, title: str, category: str, image_urls: list, catch_copy: str) -> str:
    """
    アイキャッチHTML生成。
    """
    imgs_html = ""
    target_count = min(6, len(image_urls))
    for url in image_urls[:target_count]:
        imgs_html += f'<div class="pw"><img src="{url}" class="pi" alt="" loading="eager" /></div>\n'
    for _ in range(max(0, 6 - target_count)):
        imgs_html += '<div class="pw"></div>\n'
    
    display_title = format_eyecatch_title(title)
    line_count = display_title.count("<br />") + 1
    font_size = "85px" if line_count >= 3 else ("110px" if len(title) <= 15 else "90px" if len(title) <= 22 else "85px")
    
    css = f"""@import url('https://fonts.googleapis.com/css2?family=M+PLUS+Rounded+1c:wght@800;900&display=swap');
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
html, body {{ width: 1200px; height: 630px; overflow: hidden; background: #fff; }}
body {{ font-family: 'M PLUS Rounded 1c', sans-serif; display: flex; align-items: center; justify-content: center; position: relative; }}
.g {{ display: grid; grid-template-columns: repeat(3, 1fr); grid-template-rows: repeat(2, 1fr); width: 1200px; height: 630px; padding: 20px; gap: 20px; }}
.pw {{ width: 100%; height: 100%; display: flex; align-items: center; justify-content: center; }}
.pi {{ max-width: 360px; max-height: 280px; object-fit: contain; mix-blend-mode: multiply; }}
.to {{ position: absolute; inset: 0; display: flex; align-items: center; justify-content: center; z-index: 100; pointer-events: none; }}
.ti {{ font-size: {font_size}; font-weight: 900; color: #000; line-height: 1.3; text-align: center; width: 100%; padding: 0 60px; text-shadow: 0 0 20px #fff, 0 0 20px #fff, 0 0 20px #fff; word-break: keep-all; }}
"""
    html = f"""<!DOCTYPE html>
<html lang="ja"><head><meta charset="UTF-8" /><style>{css}</style></head><body>
<div class="g">{imgs_html}</div>
<div class="to"><h1 class="ti">{display_title}</h1></div>
</body></html>"""
    path = f"public/eyecatch/{slug}.html"
    with open(path, 'w', encoding='utf-8') as f: f.write(html)
    return path

def take_eyecatch_screenshot(slug: str) -> bool:
    """
    generate-eyecatch.js を呼び出してスクリーンショットを撮る。
    """
    node_bin = "node"
    script = "scripts/generate-eyecatch.js"
    try:
        result = subprocess.run(
            [node_bin, script, slug],
            capture_output=True, text=True, timeout=90
        )
        if result.returncode != 0:
            print(f"⚠️  eyecatch stderr: {result.stderr[:500]}")
        else:
            print(f"✅ Eyecatch screenshot done for: {slug}")
        return result.returncode == 0
    except Exception as e:
        print(f"❌ Eyecatch screenshot failed: {e}")
        return False

def clean_rakuten_url(url: str) -> str:
    if not url or url == "なし":
        return ""
    cleaned = url
    cleaned = re.sub(r'[?&]m=[^&]*', '', cleaned)
    cleaned = re.sub(r'[?&]rafcid=[^&]*', '', cleaned)
    cleaned = cleaned.replace("?&", "?").rstrip("?&")
    return cleaned

def clean_yahoo_url(url: str, product_name: str) -> str:
    if not url or url == "なし":
        return ""
    
    if "shopping.yahoo.co.jp/product/" in url or "/product/j/" in url:
        query = urllib.parse.quote(product_name, safe='')
        url = f"https://shopping.yahoo.co.jp/search?p={query}"
        
    if "valuecommerce.com" in url:
        if "vc_url=" in url:
            parts = url.split("vc_url=")
            decoded_vc = urllib.parse.unquote(parts[1])
            url = parts[0] + "vc_url=" + urllib.parse.quote(decoded_vc, safe='')
    else:
        url = f"https://ck.jp.ap.valuecommerce.com/servlet/referral?sid=3767611&pid=2201292&vc_url={urllib.parse.quote(url, safe='')}"
        
    return url

def get_notion_data(article_title: str):
    script_dir = os.path.dirname(os.path.abspath(__file__))
    stockpile_path = os.path.join(script_dir, "stockpile_data.json")
    
    if not os.path.exists(stockpile_path):
        print(f"❌ Error: stockpile_data.json not found at {stockpile_path}")
        return []
        
    try:
        with open(stockpile_path, 'r', encoding='utf-8') as f:
            stockpile_data = json.load(f)
    except Exception as e:
        print(f"❌ Error reading stockpile_data.json: {e}")
        return []
        
    json_title = stockpile_data.get("category", "")
    print(f"📖 Loaded local stockpile data for article: '{json_title}'")
        
    products = []
    category = stockpile_data.get("category", "美容・スキンケア")
    json_products = stockpile_data.get("products", [])
    
    for i, p in enumerate(json_products):
        resolved = p.get("resolved_details", p)
        
        raw_name = p.get("name", "")
        clean_name = re.sub(r'\s+', ' ', raw_name).strip()
        
        item_id = p.get("id") or f"stockpile_{i + 1}"
        
        products.append({
            "id": item_id,
            "name": clean_name,
            "image_url": resolved.get("image_url") or "",
            "amazon_url": resolved.get("amazon_url") or "",
            "rakuten_url": clean_rakuten_url(resolved.get("rakuten_url") or ""),
            "yahoo_url": "",
            "amazon_price": str(resolved.get("amazon_price", "なし")),
            "rakuten_price": str(resolved.get("rakuten_price", "なし")),
            "yahoo_price": "なし",
            "category": category,
            "facts": p.get("facts", []),
            "recommended_for": p.get("recommended_for", [])
        })
    return products

def truncate_product_name(name: str) -> str:
    keywords = [" 美容液", " 保湿", " 乾燥", " うるおい", " キメ", " ツヤ", " 毛穴", " しみ", " そばかす", " ごわつき", " くすみ", " 日本製", " 30g", " 150ml", " 40ml", " 15ml"]
    short_name = name
    for kw in keywords:
        if kw in name:
            idx = name.find(kw)
            if idx > 8:
                short_name = name[:idx].strip()
                break
    if len(short_name) > 45:
        short_name = short_name[:42] + "..."
    return short_name

# PR開示テキスト（記事の最上部に1回だけ表示）
PR_DISCLOSURE = "※本記事はアフィリエイト広告を含みます。"

def run_publish(article_title: str, category: str = None, slug: str = None, publish_date: str = None):
    print(f"🚀 Processing: {article_title}")
    products = get_notion_data(article_title)
    if not products: return False
    products = products[:6]
    category = category or products[0].get("category", "ガジェット")
    
    ALLOWED_CATEGORIES = ["インテリア", "生活雑貨", "便利グッズ", "ガジェット", "美容・スキンケア"]
    if category not in ALLOWED_CATEGORIES:
        if "ガーデニング" in category or "植物" in category or "花" in category or "ライト" in category:
            category = "生活雑貨"
        else:
            category = "便利グッズ"

    # article_draft.jsonを読み込み、バリデーションを実行
    import sys
    script_dir = os.path.dirname(os.path.abspath(__file__))
    if script_dir not in sys.path:
        sys.path.append(script_dir)
    try:
        from validate_article_draft import validate
        validate()
    except ImportError as e:
        print(f"❌ Failed to import validator: {e}")
        return False
        
    draft_path = os.path.join(os.path.dirname(script_dir), "article_draft.json")
    try:
        with open(draft_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        print(f"❌ Failed to read article_draft.json: {e}")
        return False
    
    output_title = data.get("meta", {}).get("title") or article_title.replace("2024", "2026")
    slug = slug or slugify(output_title, category, publish_date)

    intro_text = data.get("content", {}).get("intro", "")
    intro_text = intro_text.replace(PR_DISCLOSURE, "").strip()

    intro_text = clean_variable_names(intro_text)
    for p in data.get("products", []):
        p['description'] = clean_variable_names(p.get('description', ''))
    
    summary_clean = data.get("content", {}).get("summary", "").replace(PR_DISCLOSURE, "").strip()
    summary_clean = re.sub(r'<p class="pr-disclosure">.*?</p>', '', summary_clean).strip()
    data.get("content", {})['summary'] = clean_variable_names(summary_clean)

    if not publish_date:
        publish_date = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).strftime("%Y-%m-%d")

    markdown = (
        f'--- \n'
        f'title: "{output_title}"\n'
        f'coverImage: ""\n'
        f'excerpt: "{data.get("meta", {}).get("excerpt", "")}"\n'
        f'publishDate: "{publish_date}"\n'
        f'category: "{category}"\n'
        f'---\n\n'
        f'{intro_text}\n\n'
    )

    markdown += f"## ✅ 選び方のポイント\n<ul>" + "".join([f"<li>{p}</li>" for p in data.get("ui", {}).get("points", [])]) + "</ul>\n\n"

    scores = ["4.88", "4.75", "4.62", "4.51", "4.42", "4.33"]

    for i, p in enumerate(data.get("products", [])):
        notion_p = next((x for x in products if x['name'].lower() in p['name'].lower() or p['name'].lower() in x['name'].lower()), None)
        display_name = truncate_product_name(p['name'])
        
        markdown += f"### 👑 第{i+1}位: {display_name}\n"
        markdown += f"[総合評価: {scores[i]}]\n\n"
        
        if notion_p and notion_p['image_url']: 
            markdown += f"IMAGE: {notion_p['image_url']}\n"
        
        if notion_p:
            for platform in ['amazon', 'rakuten']:
                price = notion_p.get(f'{platform}_price')
                if price and price != "なし": markdown += f"{platform.upper()}_PRICE: {price}\n"
            for platform, key in [('amazon', 'asin'), ('rakuten', 'rakuten')]:
                url = notion_p.get(f'{platform}_url')
                if url: markdown += f"{key.upper()}: {url}\n"
        
        markdown += f"\n[AMAZON_LINK_HERE] [RAKUTEN_LINK_HERE]\n\n"

        formatted_desc = p.get('description', '').replace('\\n', '\n\n')
        markdown += f"{formatted_desc}\n\n"
        
        markdown += f"[AMAZON_LINK_HERE] [RAKUTEN_LINK_HERE]\n\n"
        
        pros = p.get("analysis", {}).get("pros", ["情報なし"])
        cons = p.get("analysis", {}).get("cons", ["該当情報なし"])
        markdown += ":::pro\n" + "\n".join([f"{item}" for item in pros]) + "\n:::\n"
        markdown += ":::con\n" + "\n".join([f"{item}" for item in cons]) + "\n:::\n\n"
        
        markdown += f"👤 **こんな人におすすめ！**\n"
        markdown += "\n".join([f"- {item}" for item in p.get("analysis", {}).get("recommended_for", [])]) + "\n\n"
    
    comparison_table = "## 📊 比較表\n\n| 順位 | 商品名 | 価格 | 特徴 |\n| :---: | :--- | :---: | :--- |\n"
    for idx, p in enumerate(data.get("products", [])):
        name_short = truncate_product_name(p['name'])
        notion_p = next((x for x in products if x['name'].lower() in p['name'].lower() or p['name'].lower() in x['name'].lower()), None)
        price = "なし"
        if notion_p:
            price = notion_p.get("amazon_price") or notion_p.get("rakuten_price") or "なし"
        if price and price != "なし":
            price_formatted = f"¥{int(price):,}" if price.isdigit() else price
        else:
            price_formatted = "オープン価格"
        desc = p.get('description', '')
        feature = desc[:40] + "..." if len(desc) > 40 else desc
        comparison_table += f"| 第{idx+1}位 | {name_short} | {price_formatted} | {feature} |\n"
    
    markdown += comparison_table + "\n"
    
    faq_section = "## ❓ よくある質問（FAQ）\n\n"
    faq_list = data.get("ui", {}).get("faq", [])
    if faq_list:
        for item in faq_list:
            q = item.get("question", "")
            a = item.get("answer", "")
            if q and a:
                faq_section += f"### {q}\n{a}\n\n"
    else:
        faq_templates = {
            "植物育成": [
                ("Q. 24時間つけっぱなしにするべきですか？", "A. いいえ、植物にも休眠（夜の時間）が必要です。通常は1日8〜12時間程度の照射が理想的で、タイマー機能などを活用して夜間は消灯することをおすすめします。"),
                ("Q. LEDライトと太陽光ではどちらが効果的ですか？", "A. 太陽光がベストですが、日当たりの悪い室内では植物育成用LEDライトが非常に有効です。光合成に必要な赤・青の特定の波長を強化しているため、室内でも十分に育てることができます。"),
                ("Q. ライトと植物の距離はどのくらい離せばいいですか？", "A. 製品の光量にもよりますが、一般的には15cm〜30cm程度離して設置します。近づけすぎると葉焼けの原因になり、遠すぎると効果が薄れるため、植物の様子を見ながら調整してください。")
            ],
            "水草": [
                ("Q. 24時間点灯しておく必要がありますか？", "A. いいえ、1日8時間から10時間程度の点灯が目安です。点灯時間が長すぎるとコケの大量発生の原因になるため、市販のタイマー等で規則正しく管理するのが理想的です。"),
                ("Q. 赤色や青色のLEDは必要ですか？", "A. はい、赤色の光は水草の光合成を促し、青色の光は茎や葉を太く育てる効果があります。フルスペクトルやこれら2色が強化されたライトを選ぶと失敗がありません。"),
                ("Q. 熱帯魚用の通常のライトでも水草は育ちますか？", "A. 陰性植物（アヌビアスなど）であれば通常のライトでも育ちますが、陽性水草（ヘアーグラスや有茎草など）を美しく育てるには、光量が強い専用の「水草育成LEDライト」が必要です。")
            ],
            "default": [
                ("Q. 購入後の保証期間はどのくらいですか？", "A. 一般的なメーカー製品では、購入日から1年間の動作保証がついているものがほとんどです。購入時の領収書や保証書は大切に保管してください。"),
                ("Q. 日常のお手入れで気をつけるべき点は何ですか？", "A. 湿気やほこりがたまると火災や故障の原因になります。定期的に電源プラグを抜き、乾いた柔らかい布で本体の汚れを拭き取ってください。"),
                ("Q. 電気代はどのくらいかかりますか？", "A. LED製品は非常に省エネ設計です。例えば消費電力10W of ライトを1日10時間点灯した場合、1ヶ月の電気代は約90円程度と極めてリーズナブルです。")
            ]
        }
        faq_items = faq_templates["default"]
        for k, v in faq_templates.items():
            if k in output_title:
                faq_items = v
                break
        for q, a in faq_items:
            faq_section += f"### {q}\n{a}\n\n"
        
    markdown += faq_section + "\n"

    markdown += f"## 💬 まとめ\n"
    markdown += f"{data.get('content', {}).get('summary', '')}\n\n"
    markdown += f'<p class="pr-disclosure">{PR_DISCLOSURE}</p>\n'

    path = f"src/content/articles/{slug}.md"
    with open(path, 'w', encoding='utf-8') as f: f.write(markdown)
    
    image_urls = [p['image_url'] for p in products if p.get('image_url')]
    generate_eyecatch_html(slug, output_title, category, image_urls, get_seasonal_catch_copy(category))
    take_eyecatch_screenshot(slug)
    return True

import argparse
import sys

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate and publish an article from Notion data.")
    parser.add_argument("--title", help="Title of the article in Notion")
    parser.add_argument("--category", help="Category of the article")
    parser.add_argument("--slug", help="Slug/URL for the article")
    parser.add_argument("--date", help="Publish date of the article")
    
    args = parser.parse_args()
    
    if args.title:
        success = run_publish(args.title, args.category, args.slug, args.date)
        if not success:
            sys.exit(1)
    else:
        parser.print_help()
