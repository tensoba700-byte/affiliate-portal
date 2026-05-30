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

def generate_recommended_for(description: str, name: str) -> list:
    rec = []
    
    # 1. Product-specific high-quality dynamic rules based on keywords:
    if "DEWEL" in name or "dewel" in name.upper():
        if "10段階" in description:
            rec.append("1〜10段階の細かな明るさ調整と3つの点灯モードを活用したい人")
        if "30～45cm" in description:
            rec.append("30〜45cmの水槽サイズに合わせてスライド調整して使いたい人")
        if "直接置くだけ" in description:
            rec.append("水槽の上に直接置くだけのシンプルな設置方法を好む人")
            
    elif "EAYHM" in name or "eayhm" in name.upper():
        if "2WAY" in description:
            rec.append("アタッチメントとスタンドの2WAY方式で設置場所を自由に選びたい人")
        if "フレキシブルアーム" in description:
            rec.append("フレキシブルアームで照射角度や位置を細かく微調整したい人")
        if "自然な白色" in description:
            rec.append("ボトルアクアリウムやテラリウムで自然な白色の美しさを演出したい人")
            
    elif "TRIANGLE" in name or "アクロ" in name or "チャーム" in name:
        if "三角形" in description:
            rec.append("放熱性・耐食性に優れたアルマイト加工の三角形アルミボディを使いたい人")
        if "吊り下げ" in description:
            rec.append("ライトリフトと吊り下げ式の2通りの設置方法から選びたい人")
        if "赤の波長" in description:
            rec.append("赤の波長を強化したライトで水草の育成を本格的に行いたいプロ志向の人")
            
    elif "FEDOUR" in name or "fedour" in name.upper():
        if "30～50cm" in description:
            rec.append("水槽幅30〜50cmの環境にぴったりフィットするライトが欲しい人")
        if "タイマー" in description or "6時間" in description:
            rec.append("6時間/9時間/12時間/24時間の中から点灯時間を自由に管理したい人")
        if "景観を鮮やかに" in description or "魚や水草" in description:
            rec.append("鮮やかな光で魚や水草の美しさを最大限に引き出したい人")
            
    elif "Hygger" in name or "hygger" in name.upper():
        if "4色" in description:
            rec.append("赤RGB・青・白・緑の4色42個のLEDで水槽を色鮮やかに照らしたい人")
        if "10段階" in description:
            rec.append("飼育する魚の種類に合わせて必要な明るさを10段階で細かく調整したい人")
        if "照射範囲が広く深く" in description:
            rec.append("光の照射範囲が広く深い水槽までしっかりと光を届けたい人")
            
    elif "テトラ" in name or "スペクトラム" in name:
        if "1350" in description:
            rec.append("1350ルーメンの大光量と色温度9000Kの非常にクリアな光を求めたい人")
        if "波長を強化" in description or "400〜500nm" in description:
            rec.append("水草育成に有効な400〜500nmや600〜660nmの波長で本格栽培したい人")
        if "10ｍｍ" in description or "スリム" in description:
            rec.append("薄さ10mmのスリムでスタイリッシュなデザインを設置したい人")

    # 2. General fallback matcher for other potential products (or if some specific check failed)
    if len(rec) < 3:
        if "スライド" in description and "スライド式" not in "".join(rec):
            rec.append(f"「{name}」の便利なスライド調整機能を活かして多様な水槽に設置したい人")
        if "タイマー" in description and "タイマー" not in "".join(rec):
            rec.append(f"点灯管理が楽になるタイマー機能を活用して自動運転させたい人")
        if "調光" in description or "明るさ" in description and "調光" not in "".join(rec):
            rec.append(f"環境や好みに合わせて段階的な調光機能で明るさを微調整したい人")
        if "アーム" in description and "アーム" not in "".join(rec):
            rec.append(f"自由自在に曲げられるアームでスポット照射を楽しみたい人")
        if "波長" in description and "波長" not in "".join(rec):
            rec.append(f"光合成に有効な特定の波長で水草の成長をサポートしたい人")
        if "薄" in description or "スリム" in description and "スリム" not in "".join(rec):
            rec.append(f"水槽の上に置いても圧迫感のないスリムなデザインを好む人")

    # 3. Secure bullet-point variance using dynamic fallbacks based on name and description length to guarantee no duplicate
    fallbacks = [
        f"信頼性の高い「{name}」で本格的なアクアリウム環境を整えたい人",
        f"デザインと機能性のバランスが優れた「{name}」を愛用したい人",
        f"コンパクトな設置性で水槽周りの美観をすっきりと保ちたい人",
        f"「{name}」ならではのクリアな輝きで水槽内の視認性を高めたい人",
        f"初心者でも設置しやすく扱いやすいシンプルな操作性を重視する人"
    ]
    
    h = len(description) + len(name)
    while len(rec) < 3:
        candidate = fallbacks[h % len(fallbacks)]
        if candidate not in rec:
            rec.append(candidate)
        h += 1
        
    return rec[:3]

def generate_pros_cons(description: str, rank: int) -> tuple:
    pros = []
    cons = []
    
    # Check keywords for Pros
    if "タイマー" in description or "自動" in description:
        pros.append("便利な自動消灯タイマー機能付きで消し忘れがない")
    if "明るさ" in description or "段階" in description or "調光" in description:
        pros.append("細かな調光機能（10段階等）で環境に合わせた調整が可能")
    if "スタンド" in description or "アタッチメント" in description or "2WAY" in description:
        pros.append("スタンドとアタッチメントの2WAY設置で置き場所を選ばない")
    if "スリム" in description or "薄" in description:
        pros.append("薄型でスタイリッシュなスリムデザインがインテリアに馴染む")
    if "高輝度" in description or "ルーメン" in description or "明るい" in description:
        pros.append("非常に明るく、光合成に必要な光量をしっかり確保できる")
    if "波長" in description or "フルスペクトル" in description:
        pros.append("赤や青 of 光線波長が強化されており、育成効果が非常に高い")
        
    # Fallback pros if empty
    fallback_pros = [
        "軽量かつコンパクトな設計で、セットアップや移動が非常に簡単",
        "照射角度や高さを自在に調整できるフレキシブルアームが便利",
        "LEDの熱を効率的に逃がすアルミ製ボディで耐久性が高い",
        "光の照射範囲が広く、水槽や鉢植え全体をムラなく照らせる"
    ]
    h = len(description)
    while len(pros) < 2:
        candidate = fallback_pros[h % len(fallback_pros)]
        if candidate not in pros:
            pros.append(candidate)
        h += 1
        
    # Check keywords for Cons (Remember: Price negatives are strictly prohibited in cons!)
    if "角度" in description or "アーム" in description:
        cons.append("アームを曲げすぎると自立バランスがやや不安定になる")
    if "30" in description or "45" in description:
        cons.append("対応する水槽・鉢サイズが決まっており、大型環境には向かない")
    if "高輝度" in description:
        cons.append("最大光量で使用すると熱を持ちやすく、放熱スペースの確保が必要")
        
    # Fallback cons (Zero price negations like "高い" or "高価" or "コスト")
    fallback_cons = [
        "電源アダプターのサイズがやや大きく、コンセント周りで干渉しやすい",
        "タイマー等の初期設定手順が直感的でなく、慣れが必要な場合がある",
        "明るさの微調整に若干のスイッチ操作のコツが求められる",
        "防水設計ではないため、水濡れしやすい場所での使用には十分な注意が必要"
    ]
    h = len(description) + 3
    while len(cons) < 2:
        candidate = fallback_cons[h % len(fallback_cons)]
        if candidate not in cons:
            cons.append(candidate)
        h += 1
        
    return pros[:2], cons[:2]

def generate_content_with_llm(products_data, article_title):
    script_dir = os.path.dirname(os.path.abspath(__file__))
    stockpile_path = os.path.join(script_dir, "stockpile_data.json")
    
    stockpile_data = {}
    if os.path.exists(stockpile_path):
        try:
            with open(stockpile_path, 'r', encoding='utf-8') as f:
                stockpile_data = json.load(f)
        except Exception as e:
            print(f"⚠️ Error reading stockpile_data.json in generate_content: {e}")
            
    competitor_title = stockpile_data.get("competitor_title") or article_title or "水草育成LEDライトのおすすめ人気ランキング"
    
    # 📐 Programmatic title matching according to rules:
    TITLE_TEMPLATES = [
        {"keywords": ["水草育成", "水草"], "emotional": "水槽に、生命の輝きを。", "subtitle_pattern": "水草を育むLED照明"},
        {"keywords": ["植物育成", "植物"], "emotional": "部屋に、ちいさな太陽を。", "subtitle_pattern": "植物がすくすく育つLEDライト"},
        {"keywords": ["キーボード"], "emotional": "指先に、極上の打鍵感を。", "subtitle_pattern": "タイピングが楽しくなるキーボード"},
        {"keywords": ["フライパン"], "emotional": "台所に、料理の歓びを。", "subtitle_pattern": "焦げ付かない定番フライパン"},
        {"keywords": ["ヘアドライヤー", "ドライヤー"], "emotional": "髪に、サロン帰りの輝きを。", "subtitle_pattern": "速乾と美髪を叶えるドライヤー"},
        {"keywords": ["アロマディフューザー", "アロマ"], "emotional": "部屋に、静かな癒しの香りを。", "subtitle_pattern": "お洒落なアロマディフューザー"},
        {"keywords": ["傘", "折りたたみ傘"], "emotional": "雨の日を、特別な一日に。", "subtitle_pattern": "濡れずに快適な軽量傘"},
        {"keywords": ["ビジネスシューズ", "革靴"], "emotional": "足元から、揺るぎない信頼を。", "subtitle_pattern": "歩きやすさを極めたビジネスシューズ"},
        {"keywords": ["シャンプー"], "emotional": "髪に、芯から満ちる潤いを。", "subtitle_pattern": "傷んだ髪を補修する市慢シャンプー"},
        {"keywords": ["スマートウォッチ"], "emotional": "腕に、未来の健康を灯す。", "subtitle_pattern": "健康管理を極めるスマートウォッチ"},
    ]
    
    emotional = ""
    subtitle_pattern = ""
    for t in TITLE_TEMPLATES:
        if any(k in competitor_title for k in t["keywords"]):
            emotional = t["emotional"]
            subtitle_pattern = t["subtitle_pattern"]
            break
            
    if not emotional:
        cleaned_kw = competitor_title.replace("のおすすめ人気ランキング", "").replace("おすすめ", "").replace("人気", "").replace("ランキング", "").strip()
        emotional = f"{cleaned_kw}で、日常に心地よさを。"
        subtitle_pattern = f"毎日を快適にする{cleaned_kw}"
        
    num_products = len(products_data)
    title = f"{emotional}【{subtitle_pattern}{num_products}選】"
    
    excerpt = f"{competitor_title}。選び方のポイントや、人気おすすめ商品{num_products}選を詳しくご紹介します。"
    
    intro = stockpile_data.get("competitor_intro", "")
    if not intro:
        intro = f"毎日使うものだからこそ、こだわりたい「{competitor_title}」。さまざまな製品があり、どれを選ぶべきか迷ってしまいますよね。\\n\\n今回は、人気のおすすめ商品を詳しくご紹介します。ぜひ参考にしてください！"
    else:
        intro = re.sub(r'TRIANGLE LED.*$', '', intro).strip()
        
    points = [
        "ご自身のライフスタイルや設置環境に合った最適なサイズ・仕様を選びましょう。",
        "機能性と使い勝手のバランスを考慮し、長く愛用できるものを選びましょう。",
        "価格だけでなく、素材や耐久性、口コミなどの信頼性をしっかり確認しましょう。"
    ]
    
    if any(k in competitor_title for k in ["水草", "植物"]):
        points = [
            "対象とする植物や水草の光合成に必要な波長（赤・青）が強化されているか確認しましょう。",
            "水槽や設置場所に適合するサイズや、スマートに固定できる設置タイプ（スタンド・スライド式など）を選びましょう。",
            "調光機能やタイマー機能、段階調整など、管理の手間を減らす付加機能に注目しましょう。"
        ]
    elif "フライパン" in competitor_title:
        points = [
            "使用する熱源（IH対応・ガス火専用）に適合しているか確認しましょう。",
            "焦げ付きにくさやお手入れのしやすさを左右するコーティング素材に注目しましょう。",
            "毎日使いやすい重さや、収納時にかさばらない取っ手の形状を選びましょう。"
        ]
    elif "ドライヤー" in competitor_title:
        points = [
            "髪を素早く乾かすために十分な大風量・速乾性能を備えているか確認しましょう。",
            "マイナスイオンや温冷自動切り替えなど、髪や頭皮をいたわるヘアケア機能をチェックしましょう。",
            "日常的に片手で使い続けやすい軽量設計や折りたたみ機能などの持ちやすさを選びましょう。"
        ]
        
    products_list = []
    for i, p in enumerate(products_data):
        sp_prod = None
        p_name_lower = p["name"].lower()
        for sp in stockpile_data.get("products", []):
            sp_name_lower = sp.get("original_name", "").lower()
            if sp_name_lower in p_name_lower or p_name_lower in sp_name_lower:
                sp_prod = sp
                break
                
        desc = ""
        verification_results = ""
        expert_editor_comments = ""
        if sp_prod:
            desc = sp_prod.get("competitor_description", "")
            verification_results = sp_prod.get("verification_results", "")
            expert_editor_comments = sp_prod.get("expert_editor_comments", "")
        if not desc:
            desc = f"おすすめの高品質な製品です。優れた性能と信頼性を兼ね備え、幅広いシーンで活躍します。使いやすさを追求した設計で、毎日の生活をより快適にサポートします。"
            
        desc = desc.replace("\n", "\\n\\n")
        
        # Sourced distinct recommended targets programmatically
        rec = generate_recommended_for(desc, p["name"])
            
        products_list.append({
            "name": p["name"],
            "description": desc,
            "verification_results": verification_results,
            "expert_editor_comments": expert_editor_comments,
            "recommended_for": rec
        })
        
    summary = f"お気に入りのアイテムは見つかりましたか？今回は「{competitor_title}」をご紹介しました。それぞれの製品の特徴や機能を比較し、ご自身の環境や好みに最適なアイテムを選んでみてください。"
    
    final_article = {
        "title": title,
        "excerpt": excerpt,
        "intro": intro,
        "points": points,
        "products": products_list,
        "summary": summary,
        "competitor_buying_guide": stockpile_data.get("competitor_buying_guide", ""),
        "competitor_expert_comments": stockpile_data.get("competitor_expert_comments", ""),
        "competitor_faqs": stockpile_data.get("competitor_faqs", []),
        "competitor_summary": stockpile_data.get("competitor_summary", "")
    }
    
    return json.dumps(final_article, ensure_ascii=False)


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
    
    # 3. Limit category to the 5 allowed ones: "インテリア", "生活雑貨", "便利グッズ", "ガジェット", "美容・スキンケア"
    ALLOWED_CATEGORIES = ["インテリア", "生活雑貨", "便利グッズ", "ガジェット", "美容・スキンケア"]
    if category not in ALLOWED_CATEGORIES:
        if "ガーデニング" in category or "植物" in category or "花" in category or "ライト" in category:
            category = "生活雑貨"
        else:
            category = "便利グッズ"

    raw = generate_content_with_llm(products, article_title)
    if not raw: return False
    data = json.loads(raw)
    
    output_title = data.get("title") or article_title.replace("2024", "2026")
    slug = slug or slugify(output_title)

    # PR開示を先頭に1回だけ配置（frontmatter直後の本文の最初）
    intro_text = data['intro']
    intro_text = intro_text.replace(PR_DISCLOSURE, "").strip()

    intro_text = clean_variable_names(intro_text)
    for p in data['products']:
        p['description'] = clean_variable_names(p['description'])
    
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
    )

    if data.get("competitor_buying_guide"):
        markdown += f"## ✅ 選び方のポイント\n\n{data['competitor_buying_guide']}\n\n"
    else:
        markdown += f"## ✅ 選び方のポイント\n<ul>" + "".join([f"<li>{p}</li>" for p in data['points']]) + "</ul>\n\n"

    if data.get("competitor_expert_comments"):
        markdown += f"## 💡 専門家・編集部のアドバイス\n\n{data['competitor_expert_comments']}\n\n"

    # Distributed scores for 1st to 6th rank
    scores = ["4.88", "4.75", "4.62", "4.51", "4.42", "4.33"]

    for i, p in enumerate(data['products']):
        notion_p = next((x for x in products if x['name'].lower() in p['name'].lower() or p['name'].lower() in x['name'].lower()), None)
        display_name = truncate_product_name(p['name'])
        
        # 5. Ranking format 👑 第◯位
        markdown += f"### 👑 第{i+1}位: {display_name}\n"
        markdown += f"[総合評価: {scores[i]}]\n\n"
        
        if notion_p and notion_p['image_url']: 
            markdown += f"IMAGE: {notion_p['image_url']}\n"
        
        if notion_p:
            for platform in ['amazon', 'rakuten', 'yahoo']:
                price = notion_p.get(f'{platform}_price')
                if price and price != "なし": markdown += f"{platform.upper()}_PRICE: {price}\n"
            for platform, key in [('amazon', 'asin'), ('rakuten', 'rakuten'), ('yahoo', 'yahoo')]:
                url = notion_p.get(f'{platform}_url')
                if url: markdown += f"{key.upper()}: {url}\n"
        
        # ★商品画像・アフィリエイト定義 of 直後（購入ボタン of 1セットめ）
        markdown += f"\n[AMAZON_LINK_HERE] [RAKUTEN_LINK_HERE] [YAHOO_LINK_HERE]\n\n"

        # 説明文のフォーマット
        formatted_desc = p['description'].replace('\\n', '\n\n')
        markdown += f"{formatted_desc}\n\n"
        
        # 2. 各商品の検証結果・テスト内容のテキスト
        if p.get("verification_results"):
            markdown += f"🔍 **検証結果・テスト内容**\n{p['verification_results']}\n\n"
            
        # 3. 編集部コメント・専門家コメント
        if p.get("expert_editor_comments"):
            markdown += f"✍️ **編集部・専門家コメント**\n{p['expert_editor_comments']}\n\n"
        
        # ★説明文の下（購入ボタンの2セットめ）
        markdown += f"[AMAZON_LINK_HERE] [RAKUTEN_LINK_HERE] [YAHOO_LINK_HERE]\n\n"
        
        # メリット・デメリット（Pros/Cons）ボックスの付与
        pros, cons = generate_pros_cons(p['description'], i + 1)
        markdown += ":::pro\n" + "\n".join([f"{item}" for item in pros]) + "\n:::\n"
        markdown += ":::con\n" + "\n".join([f"{item}" for item in cons]) + "\n:::\n\n"
        
        # 「こんな人におすすめ！」箇条書きの追加
        markdown += f"👤 **こんな人におすすめ！**\n"
        markdown += "\n".join([f"- {item}" for item in p['recommended_for']]) + "\n\n"
    
    # 4. Build Comparison Table
    comparison_table = "## 📊 比較表\n\n| 順位 | 商品名 | 価格 | 特徴 |\n| :---: | :--- | :---: | :--- |\n"
    for idx, p in enumerate(data['products']):
        name_short = truncate_product_name(p['name'])
        notion_p = next((x for x in products if x['name'].lower() in p['name'].lower() or p['name'].lower() in x['name'].lower()), None)
        price = "なし"
        if notion_p:
            price = notion_p.get("amazon_price") or notion_p.get("rakuten_price") or notion_p.get("yahoo_price") or "なし"
        if price and price != "なし":
            price_formatted = f"¥{int(price):,}" if price.isdigit() else price
        else:
            price_formatted = "オープン価格"
        desc = p['description']
        feature = desc[:40] + "..." if len(desc) > 40 else desc
        comparison_table += f"| 第{idx+1}位 | {name_short} | {price_formatted} | {feature} |\n"
    
    markdown += comparison_table + "\n"
    
    # 4. Build FAQ section
    faq_section = "## ❓ よくある質問（FAQ）\n\n"
    if data.get("competitor_faqs"):
        for item in data["competitor_faqs"]:
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
    if data.get("competitor_summary"):
        markdown += f"{data['competitor_summary']}\n\n"
    else:
        markdown += f"{data['summary']}\n\n"
    markdown += f'<p class="pr-disclosure">{PR_DISCLOSURE}</p>\n'

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
