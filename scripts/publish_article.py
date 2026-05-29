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
load_dotenv(".env.local")
# For local bot development (optional/ignored if not found)
load_dotenv(os.path.expanduser("~/.gemini/antigravity/scratch/discord-bot/.env"))

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


def slugify(text: str) -> str:
    """Generate a filename-friendly slug from title."""
    text = text.replace("2024", "2026")
    text = re.sub(r'[^\w\s-]', '', text).strip().lower()
    text = re.sub(r'[-\s]+', '-', text)
    jst = datetime.timezone(datetime.timedelta(hours=9))
    date_prefix = datetime.datetime.now(jst).strftime("%Y%m%d")
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

def format_eyecatch_title(title: str) -> str:
    """
    アイキャッチ用タイトルを3行に整形する。
    対象形式: [情緒]。【[機能的説明][商品カテゴリ][N]選】
    出力:
      Line1: [情緒]         （句点なし）
      Line2: [機能的説明]   （括弧なし）
      Line3: 【[カテゴリN選]】 （3行目だけ括弧）
    """
    import re
    # メインパターン: 情緒。【機能説明 + 商品N選】
    m = re.match(r'^(.+?)。【(.+?)(\d+選)】$', title)
    if m:
        emotional   = m.group(1)  # 例: 髪に、潤いと輝きを
        description = m.group(2)  # 例: 傷んだ髪を補修する市販シャンプー
        count_part  = m.group(3)  # 例: 6選
        # ひらがな末尾 → 漢字/カタカナ先頭の境界で分割
        split_m = re.search(
            r'^(.*[\u3041-\u3096])([\u4e00-\u9fff\u30a0-\u30ff].+)$',
            description
        )
        if split_m:
            line2 = split_m.group(1)  # 傷んだ髪を補修する
            line3 = f'【{split_m.group(2)}{count_part}】'  # 【市販シャンプー6選】
        else:
            line2 = description
            line3 = f'【{count_part}】'
        return f'{emotional}<br />{line2}<br />{line3}'
    # フォールバック: パターンに合わない場合は中間で１回改行
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
    generate-eyecatch.js 側でページロード後に全画像の完了を待ってからスクリーンショットを撮るため、
    ここでは正確なHTMLを生成するのみ。
    """
    imgs_html = ""
    target_count = min(6, len(image_urls))
    for url in image_urls[:target_count]:
        imgs_html += f'<div class="pw"><img src="{url}" class="pi" alt="" loading="eager" /></div>\n'
    # Fill remaining slots to maintain 3x2 grid
    for _ in range(max(0, 6 - target_count)):
        imgs_html += '<div class="pw"></div>\n'
    
    # Format title with line breaks and adjust size for long text
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
    generate-eyecatch.js 内部で networkidle0 + 全img完了待機を行っているため
    ここでは単純に呼び出すだけでよい。
    """
    node_bin = "node"  # Use system node in CI/Local
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
    # Strip &m=... and &rafcid=... parameters to prevent mobile redirection freezes
    cleaned = url
    cleaned = re.sub(r'[?&]m=[^&]*', '', cleaned)
    cleaned = re.sub(r'[?&]rafcid=[^&]*', '', cleaned)
    # If the URL now has a trailing ? or multiple &, clean it up
    cleaned = cleaned.replace("?&", "?").rstrip("?&")
    return cleaned

def clean_yahoo_url(url: str, product_name: str) -> str:
    if not url or url == "なし":
        return ""
    
    # 1. Avoid shopping.yahoo.co.jp/product/ or /product/j/ to prevent ValueCommerce errors
    if "shopping.yahoo.co.jp/product/" in url or "/product/j/" in url:
        # Fallback to search query
        query = urllib.parse.quote(product_name)
        url = f"https://shopping.yahoo.co.jp/search?p={query}"
        
    # 2. Check if it's already a ValueCommerce link
    if "valuecommerce.com" in url:
        if "vc_url=" in url:
            parts = url.split("vc_url=")
            # Re-encode the vc_url query param
            decoded_vc = urllib.parse.unquote(parts[1])
            url = parts[0] + "vc_url=" + urllib.parse.quote(decoded_vc)
    else:
        # It's a direct Yahoo Shopping link, wrap it with ValueCommerce
        url = f"https://ck.jp.ap.valuecommerce.com/servlet/referral?sid=3767611&pid=2201292&vc_url={urllib.parse.quote(url)}"
        
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
        
    json_title = stockpile_data.get("default_title", "")
    print(f"📖 Loaded local stockpile data for article: '{json_title}'")
    if article_title.strip() != json_title.strip():
        print(f"⚠️ Warning: Requested article_title '{article_title}' does not exactly match default_title '{json_title}' in stockpile_data.json.")
        
    products = []
    category = stockpile_data.get("default_category", "ガジェット")
    json_products = stockpile_data.get("products", [])
    
    for i, p in enumerate(json_products):
        resolved = p.get("resolved_details", {})
        
        # Clean product name: remove newlines or extra spaces
        raw_name = p.get("original_name", "")
        clean_name = re.sub(r'\s+', ' ', raw_name).strip()
        
        # We also need an ID
        item_id = p.get("id") or f"stockpile_{p.get('rank', i + 1)}"
        
        products.append({
            "id": item_id,
            "name": clean_name,
            "image_url": resolved.get("image_url") or "",
            "amazon_url": resolved.get("amazon_url") or "",
            "rakuten_url": clean_rakuten_url(resolved.get("rakuten_url") or ""),
            "yahoo_url": clean_yahoo_url(resolved.get("yahoo_url") or "", clean_name),
            "amazon_price": str(resolved.get("amazon_price", "なし")),
            "rakuten_price": str(resolved.get("rakuten_price", "なし")),
            "yahoo_price": str(resolved.get("yahoo_price", "なし")),
            "category": category
        })
    return products

def generate_content_with_llm(products_data, article_title):
    # GENERATION_RULES.md を読み込む
    rules_text = load_generation_rules()
    rules_section = f"\n\n【記事生成ルール（必ず遵守）】\n{rules_text}" if rules_text else ""

    llm_products = [{"name": p["name"]} for p in products_data]
    prompt = f"""あなたはプロのWebライターとして、中立的かつ信頼性の高い商品紹介記事を執筆してください。
読者に親しみやすさを感じさせつつも、過度な装飾やAI特有の極端な表現を避けた、誠実なトーンを維持してください。
{rules_section}

【厳守事項】
0. **本記事は【🌸 A. 並列（Parallel）モード】で作成します。**
1. **ランキング形式の禁止**: 全ての商品を「おすすめの選択肢」として並列に扱ってください。順位や「第○位」という表現は一切使わないでください。
2. **NGワード**: 「マジで」「ヤバい」「神アイテム」「最高」「究極」などの煽り文句や、過剰な強調表現は使用禁止です。
3. **一人称の禁止**: 「おこげ」「私」といった一人称や個人の体験談を装った記述は全て削除してください。
4. **商品説明の制限**: 各商品の紹介（description）は、**600〜800文字程度**で、特徴・使用感・効果を具体的に詳しく説明してください。（出力上限内に収めるため、800文字を超えすぎないよう厳守してください）
5. **絵文字の活用**: 各見出しおよび商品説明において、絵文字は**1商品につき1〜2個まで**に制限してください。
6. **ターゲット層**: 各商品に対し、「こんな人におすすめ！」という項目で、具体的な推奨理由を**3つの箇条書き**で作成してください。
7. **変数名禁止**: YAHOO_PRICE・RAKUTEN_PRICE・AMAZON_PRICE・YAHOOなどの変数名を文中に絶対に含めないでください。
8. **段落分け**: 各段落は**1〜2文程度**とし、段落間には空行（\n\n）を入れてスマホで最も読みやすい構成にしてください。また、文章が長く繋がらないように配慮してください。

2026年時点の最新トレンドを踏まえ、以下の商品{len(llm_products)}点のおすすめ紹介記事をJSONで作成してください。
URLや価格は含めないでください。

{json.dumps(llm_products, ensure_ascii=False)}

出力形式: {{"excerpt": "...", "intro": "...", "points": ["...", "...", "..."], "products": [{{"name": "...", "description": "...", "recommended_for": ["...", "...", "..."]}}], "summary": "..."}}"""
    
    model = genai.GenerativeModel('models/gemini-2.5-flash')
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

def truncate_product_name(name: str) -> str:
    # Remove SEO keywords and long descriptions to keep the title concise
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

def run_publish(article_title: str, category: str = None, slug: str = None):
    print(f"🚀 Processing: {article_title}")
    products = get_notion_data(article_title)
    if not products: return False
    # 固定で6個にする
    products = products[:6]
    category = category or products[0].get("category", "ガジェット")
    output_title = article_title.replace("2024", "2026")
    slug = slug or slugify(article_title)
    raw = generate_content_with_llm(products, output_title)
    if not raw: return False
    data = json.loads(raw)

    # PR開示を先頭に1回だけ配置（frontmatter直後の本文の最初）
    intro_text = data['intro']
    # 念のため intro_text からPR開示の重複を除去
    intro_text = intro_text.replace(PR_DISCLOSURE, "").strip()

    # 変数名クリーニング（LLMが出力してしまった場合に備えて）
    intro_text = clean_variable_names(intro_text)
    for p in data['products']:
        p['description'] = clean_variable_names(p['description'])
    # 念のため summary からPR開示の重複を除去
    summary_clean = data['summary'].replace(PR_DISCLOSURE, "").strip()
    summary_clean = re.sub(r'<p class="pr-disclosure">.*?</p>', '', summary_clean).strip()
    data['summary'] = clean_variable_names(summary_clean)

    markdown = (
        f'--- \n'
        f'title: "{output_title}"\n'
        f'coverImage: ""\n'
        f'excerpt: "{data["excerpt"]}"\n'
        f'publishDate: "{datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).strftime("%Y-%m-%d")}"\n'
        f'category: "{category}"\n'
        f'---\n\n'
        f'{intro_text}\n\n'
        f'## ✅ 選び方のポイント\n<ul>'
        + "".join([f"<li>{p}</li>" for p in data['points']])
        + "</ul>\n\n"
    )

    for i, p in enumerate(data['products']):
        notion_p = next((x for x in products if x['name'].lower() in p['name'].lower() or p['name'].lower() in x['name'].lower()), None)
        display_name = truncate_product_name(p['name'])
        markdown += f"### 🌸 {display_name}\n"
        if notion_p and notion_p['image_url']: markdown += f"IMAGE: {notion_p['image_url']}\n"
        
        if notion_p:
            for platform in ['amazon', 'rakuten', 'yahoo']:
                price = notion_p.get(f'{platform}_price')
                if price and price != "なし": markdown += f"{platform.upper()}_PRICE: {price}\n"
            for platform, key in [('amazon', 'asin'), ('rakuten', 'rakuten'), ('yahoo', 'yahoo')]:
                url = notion_p.get(f'{platform}_url')
                if url: markdown += f"{key.upper()}: {url}\n"
        
        # ★商品画像・アフィリエイト定義の直後（購入ボタンの1セットめ）
        markdown += f"\n[AMAZON_LINK_HERE] [RAKUTEN_LINK_HERE] [YAHOO_LINK_HERE]\n\n"

        # 説明文のフォーマット（1000文字以上）
        formatted_desc = p['description'].replace('\\n', '\n\n')
        markdown += f"{formatted_desc}\n\n"
        
        # ★説明文の下（購入ボタンの2セットめ）
        markdown += f"[AMAZON_LINK_HERE] [RAKUTEN_LINK_HERE] [YAHOO_LINK_HERE]\n\n"
        
        # 「こんな人におすすめ！」箇条書きの追加
        markdown += f"👤 **こんな人におすすめ！**\n"
        markdown += "\n".join([f"- {item}" for item in p['recommended_for']]) + "\n\n"
    
    markdown += f"## 💬 まとめ\n{data['summary']}\n\n"
    markdown += f'<p class="pr-disclosure">{PR_DISCLOSURE}</p>\n'

    # Markdown全体からの変数名除去は手動で挿入したアフィリエイトURL（ASIN: 等）を消してしまうため行わない
    # markdown = clean_variable_names(markdown)

    path = f"src/content/articles/{slug}.md"
    with open(path, 'w', encoding='utf-8') as f: f.write(markdown)
    
    # アイキャッチ生成
    image_urls = [p['image_url'] for p in products if p.get('image_url')]
    generate_eyecatch_html(slug, output_title, category, image_urls, get_seasonal_catch_copy(category))
    # generate-eyecatch.js が内部で全画像読み込み完了を待ってからスクリーンショットを撮る
    take_eyecatch_screenshot(slug)
    return True

import argparse
import sys

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate and publish an article from Notion data.")
    parser.add_argument("--title", help="Title of the article in Notion")
    parser.add_argument("--category", help="Category of the article")
    parser.add_argument("--slug", help="Slug/URL for the article")
    
    args = parser.parse_args()
    
    if args.title:
        success = run_publish(args.title, args.category, args.slug)
        if not success:
            sys.exit(1)
    else:
        parser.print_help()
