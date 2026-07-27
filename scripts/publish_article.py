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
    "乳液": "emulsion",
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

def check_recent_duplicate_topic(slug: str, days: int = 21) -> str:
    """
    直近days日以内に同じ商品カテゴリ（slugの英語部分、例: cleanser, serum）の記事が
    既に公開されていないか確認する。見つかれば既存記事のslugを返し、なければ空文字を返す。
    美容・スキンケア記事の連投によるキーワードカニバリゼーション（例: 洗顔料記事が
    数日おきに複数公開される事態）を publish 前に検知するためのガード。
    """
    m = re.match(r'^(\d{8})-(.+)$', slug)
    if not m:
        return ""
    date_str, slug_part = m.groups()
    if re.match(r'^article-\d+$', slug_part):
        return ""  # カテゴリ不明時の連番slugは対象外

    try:
        new_date = datetime.datetime.strptime(date_str, "%Y%m%d")
    except ValueError:
        return ""

    articles_dir = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "src", "content", "articles"
    )
    if not os.path.isdir(articles_dir):
        return ""

    for fname in os.listdir(articles_dir):
        if not fname.endswith(".md") or fname == "GENERATION_RULES.md":
            continue
        existing_slug = fname[:-3]
        if existing_slug == slug:
            continue
        em = re.match(r'^(\d{8})-(.+)$', existing_slug)
        if not em or em.group(2) != slug_part:
            continue
        try:
            existing_date = datetime.datetime.strptime(em.group(1), "%Y%m%d")
        except ValueError:
            continue
        if abs((new_date - existing_date).days) <= days:
            return existing_slug
    return ""


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
        # 品詞や意味のまとまり（〜の選び方、〜おすすめ）を考慮した優先的分割パターン
        opt_match = re.search(r'^(.*?(?:の選び方と|の選び方|と|に|で|は|が))((?:おすすめ|人気|厳選|最新|注目).+)$', description)
        if opt_match:
            line2 = opt_match.group(1)
            line3 = f'【{opt_match.group(2)}{count_part}】'
        else:
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
    
    display_title = format_eyecatch_title(title.replace("<br>", "").replace("<br/>", "").replace("<br />", ""))
    line_count = display_title.count("<br />") + 1
    font_size = "60px" if line_count >= 3 else ("80px" if len(title) <= 15 else "68px" if len(title) <= 22 else "60px")
    
    css = f"""@import url('https://fonts.googleapis.com/css2?family=Noto+Serif+JP:wght@500;700&display=swap');
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
html, body {{ width: 1200px; height: 630px; overflow: hidden; background: #F7F7F5; }}
body {{ font-family: 'Noto Serif JP', serif; display: flex; align-items: center; justify-content: center; position: relative; }}
.g {{ display: grid; grid-template-columns: repeat(3, 1fr); grid-template-rows: repeat(2, 1fr); width: 1200px; height: 630px; padding: 20px; gap: 20px; }}
.pw {{ width: 100%; height: 100%; display: flex; align-items: center; justify-content: center; }}
.pi {{ max-width: 360px; max-height: 280px; object-fit: contain; mix-blend-mode: multiply; }}
.to {{ position: absolute; inset: 0; display: flex; align-items: center; justify-content: center; z-index: 100; pointer-events: none; }}
.ti {{ font-size: {font_size}; font-weight: 500; color: #000; line-height: 1.3; text-align: center; width: auto; max-width: 90%; padding: 30px 45px; background-color: rgba(255, 255, 255, 0.5); border-radius: 8px; word-break: keep-all; }}
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

def generate_pinterest_eyecatch_html(slug: str, title: str, category: str, image_urls: list, catch_copy: str) -> str:
    """
    Pinterest用の縦型アイキャッチHTML生成 (1000px × 1500px)。
    """
    theme = CATEGORY_THEMES.get(category, {'bg1': '#FF9EDB', 'bg2': '#FF69B4', 'accent': '#FFFFFF'})
    bg1 = theme['bg1']
    bg2 = theme['bg2']
    
    badge = extract_badge(title)
    
    # Grid images HTML
    imgs_html = ""
    target_count = min(4, len(image_urls))
    for url in image_urls[:target_count]:
        imgs_html += f'<div class="img-wrapper"><img src="{url}" alt="" loading="eager" /></div>\n'
    for _ in range(max(0, 4 - target_count)):
        imgs_html += '<div class="img-wrapper" style="box-shadow: none; background: transparent;"></div>\n'
        
    display_title = format_eyecatch_title(title.replace("<br>", "").replace("<br/>", "").replace("<br />", ""))
    
    css = f"""@import url('https://fonts.googleapis.com/css2?family=Noto+Serif+JP:wght@700;900&family=Outfit:wght@600&display=swap');
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
html, body {{ width: 1000px; height: 1500px; overflow: hidden; background: #F7F7F5; }}
body {{
  font-family: 'Noto Serif JP', serif;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: space-between;
  padding: 80px 50px;
  position: relative;
}}
.bg {{
  position: absolute;
  inset: 0;
  background: linear-gradient(135deg, {bg1} 0%, {bg2} 100%);
  opacity: 0.15;
  z-index: -1;
}}
.header-badge {{
  font-family: 'Outfit', sans-serif;
  font-size: 32px;
  font-weight: 600;
  color: #fff;
  background-color: {bg2};
  padding: 12px 36px;
  border-radius: 50px;
  text-transform: uppercase;
  letter-spacing: 2px;
  margin-bottom: 10px;
  box-shadow: 0 4px 10px rgba(0,0,0,0.1);
}}
.season-copy {{
  font-size: 28px;
  color: #555;
  font-weight: 500;
  margin-bottom: 20px;
  text-align: center;
}}
.title-container {{
  width: 100%;
  text-align: center;
  padding: 40px 30px;
  background: rgba(255, 255, 255, 0.9);
  backdrop-filter: blur(10px);
  border-radius: 16px;
  box-shadow: 0 10px 30px rgba(0,0,0,0.08);
  border: 1px solid rgba(255, 255, 255, 0.5);
  margin-bottom: 30px;
}}
.title {{
  font-size: 60px;
  font-weight: 900;
  color: #111;
  line-height: 1.35;
  word-break: keep-all;
}}
.images-grid {{
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 30px;
  width: 100%;
  flex-grow: 1;
  align-items: center;
  justify-content: center;
  max-height: 620px;
  margin-bottom: 30px;
}}
.img-wrapper {{
  background: white;
  border-radius: 12px;
  padding: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  height: 270px;
  box-shadow: 0 4px 15px rgba(0,0,0,0.05);
}}
.img-wrapper img {{
  max-width: 100%;
  max-height: 100%;
  object-fit: contain;
  mix-blend-mode: multiply;
}}
.footer {{
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
}}
.site-logo {{
  font-size: 40px;
  font-weight: 900;
  color: {bg2};
  letter-spacing: 1px;
}}
.site-url {{
  font-family: 'Outfit', sans-serif;
  font-size: 24px;
  color: #666;
  letter-spacing: 1px;
}}
"""
    html = f"""<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="UTF-8" />
  <style>{css}</style>
</head>
<body>
  <div class="bg"></div>
  <div class="header-badge">{badge}</div>
  <div class="season-copy">{catch_copy}</div>
  <div class="title-container">
    <h1 class="title">{display_title}</h1>
  </div>
  <div class="images-grid">
    {imgs_html}
  </div>
  <div class="footer">
    <div class="site-logo">Mikke!</div>
    <div class="site-url">mikke-style.com</div>
  </div>
</body>
</html>"""
    path = f"public/eyecatch/{slug}-pin.html"
    with open(path, 'w', encoding='utf-8') as f: f.write(html)
    return path

def take_pinterest_eyecatch_screenshot(slug: str) -> bool:
    """
    generate-pinterest-eyecatch.js を呼び出して 2:3 スクショを撮影する。
    """
    node_bin = "node"
    script = "scripts/generate-pinterest-eyecatch.js"
    try:
        result = subprocess.run(
            [node_bin, script, slug],
            capture_output=True, text=True, timeout=90
        )
        if result.returncode != 0:
            print(f"⚠️  pinterest-eyecatch stderr: {result.stderr[:500]}")
        else:
            print(f"✅ Pinterest Eyecatch screenshot done for: {slug}")
        return result.returncode == 0
    except Exception as e:
        print(f"❌ Pinterest Eyecatch screenshot failed: {e}")
        return False

def clean_and_convert_scraped_url(scraped_url: str, mall: str, product_name: str = "") -> str:
    """my-bestのスクレイピングURL等から、自分自身のアフィリエイトURLに再構築して返します。"""
    if not scraped_url:
        return ""
    
    parsed = urllib.parse.urlparse(scraped_url)
    qs = urllib.parse.parse_qs(parsed.query)
    
    fallback_url = qs.get("fallback_url", [""])[0]
    url_in_query = qs.get("url", [""])[0]
    
    base_url = fallback_url if fallback_url else scraped_url
    
    parsed_base = urllib.parse.urlparse(base_url)
    qs_base = urllib.parse.parse_qs(parsed_base.query)
    
    if mall == "amazon":
        asin_match = re.search(r'/dp/([A-Z0-9]{10})|/gp/product/([A-Z0-9]{10})', base_url)
        if not asin_match and url_in_query:
            asin_match = re.search(r'/dp/([A-Z0-9]{10})|/gp/product/([A-Z0-9]{10})', url_in_query)
            
        if asin_match:
            asin_val = asin_match.group(1) or asin_match.group(2)
            return f"https://www.amazon.co.jp/dp/{asin_val}?tag=mikkestyle-22"
        
        if "tag" in qs_base:
            replaced_qs = qs_base.copy()
            replaced_qs["tag"] = ["mikkestyle-22"]
            new_query = urllib.parse.urlencode(replaced_qs, doseq=True)
            return urllib.parse.urlunparse(parsed_base._replace(query=new_query))
        else:
            connector = "&" if parsed_base.query else "?"
            return f"{base_url}{connector}tag=mikkestyle-22"
            
    elif mall == "rakuten":
        rakuten_affiliate_id = "52aa350c.c59bcb5a.52aa350d.c841a8ec"
        target_url = ""
        for param in ["url", "pc", "m"]:
            if param in qs_base:
                target_url = qs_base[param][0]
                break
            if param in qs:
                target_url = qs[param][0]
                break
        
        if not target_url:
            if "rakuten.co.jp" in base_url and not "hb.afl.rakuten.co.jp" in base_url:
                target_url = base_url
            else:
                for param in ["vc_url", "u"]:
                    if param in qs_base:
                        target_url = qs_base[param][0]
                        break
        
        if not target_url:
            target_url = base_url
            
        encoded_target = urllib.parse.quote(target_url)
        raw_rak_url = f"https://hb.afl.rakuten.co.jp/ichiba/{rakuten_affiliate_id}/?pc={encoded_target}"
        return clean_rakuten_url(raw_rak_url)
        
    elif mall == "yahoo":
        yahoo_sid = "3767611"
        yahoo_pid = "2201292"
        
        target_url = ""
        for param in ["url", "vc_url", "u"]:
            if param in qs_base:
                target_url = qs_base[param][0]
                break
            if param in qs:
                target_url = qs[param][0]
                break
                
        if not target_url:
            if "yahoo.co.jp" in base_url and not "valuecommerce.com" in base_url:
                target_url = base_url
            else:
                target_url = base_url
                
        if "/product/" in target_url or "/product/j/" in target_url:
            if product_name:
                encoded_query = urllib.parse.quote(product_name, safe='')
                target_url = f"https://shopping.yahoo.co.jp/search?p={encoded_query}"

        encoded_target = urllib.parse.quote(target_url)
        return f"https://ck.jp.ap.valuecommerce.com/servlet/referral?sid={yahoo_sid}&pid={yahoo_pid}&vc_url={encoded_target}"

    return scraped_url

def clean_rakuten_url(url: str) -> str:
    if not url or url == "なし":
        return ""
    
    if "my-best.com" in url:
        return clean_and_convert_scraped_url(url, "rakuten")
        
    cleaned = url
    taro_rakuten_id = "52aa350c.c59bcb5a.52aa350d.c841a8ec"
    match = re.search(r'hb\.afl\.rakuten\.co\.jp/ichiba/([a-zA-Z0-9\._\-]+)/', cleaned)
    if match:
        current_id = match.group(1)
        if current_id != taro_rakuten_id:
            cleaned = cleaned.replace(f"/ichiba/{current_id}/", f"/ichiba/{taro_rakuten_id}/")
    else:
        if "rakuten.co.jp" in cleaned and not "hb.afl.rakuten.co.jp" in cleaned:
            encoded_target = urllib.parse.quote(cleaned)
            cleaned = f"https://hb.afl.rakuten.co.jp/ichiba/{taro_rakuten_id}/?pc={encoded_target}"

    cleaned = re.sub(r'[?&]m=[^&]*', '', cleaned)
    cleaned = re.sub(r'[?&]rafcid=[^&]*', '', cleaned)
    cleaned = cleaned.replace("?&", "?").rstrip("?&")
    return cleaned

def clean_yahoo_url(url: str, product_name: str) -> str:
    if not url or url == "なし":
        return ""
    
    if "my-best.com" in url:
        return clean_and_convert_scraped_url(url, "yahoo", product_name)
        
    cleaned = url
    yahoo_sid = "3767611"
    yahoo_pid = "2201292"
    
    if "shopping.yahoo.co.jp/product/" in cleaned or "/product/j/" in cleaned:
        query = urllib.parse.quote(product_name, safe='')
        cleaned = f"https://shopping.yahoo.co.jp/search?p={query}"
        
    if "valuecommerce.com" in cleaned:
        parsed = urllib.parse.urlparse(cleaned)
        qs = urllib.parse.parse_qs(parsed.query)
        
        sid_list = qs.get("sid", [])
        pid_list = qs.get("pid", [])
        vc_url_list = qs.get("vc_url", [])
        
        need_rebuild = False
        if not sid_list or sid_list[0] != yahoo_sid:
            need_rebuild = True
        if not pid_list or pid_list[0] != yahoo_pid:
            need_rebuild = True
            
        vc_url = vc_url_list[0] if vc_url_list else ""
        if "/product/" in vc_url or "/product/j/" in vc_url:
            query = urllib.parse.quote(product_name, safe='')
            vc_url = f"https://shopping.yahoo.co.jp/search?p={query}"
            need_rebuild = True
            
        if need_rebuild:
            if not vc_url:
                vc_url = cleaned
            
            encoded_vc = urllib.parse.quote(vc_url, safe='')
            cleaned = f"https://ck.jp.ap.valuecommerce.com/servlet/referral?sid={yahoo_sid}&pid={yahoo_pid}&vc_url={encoded_vc}"
        else:
            if "vc_url=" in cleaned:
                parts = cleaned.split("vc_url=")
                decoded_vc = urllib.parse.unquote(parts[1])
                if "/product/" in decoded_vc or "/product/j/" in decoded_vc:
                    query = urllib.parse.quote(product_name, safe='')
                    decoded_vc = f"https://shopping.yahoo.co.jp/search?p={query}"
                cleaned = parts[0] + "vc_url=" + urllib.parse.quote(decoded_vc, safe='')
    else:
        cleaned = f"https://ck.jp.ap.valuecommerce.com/servlet/referral?sid={yahoo_sid}&pid={yahoo_pid}&vc_url={urllib.parse.quote(cleaned, safe='')}"
        
    return cleaned

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
    
    # stockpile_data.jsonを読み込んで商品名でマッチングする処理を追加
    try:
        stockpile = json.load(open("scripts/stockpile_data.json"))
        stockpile_map = {p["name"]: p for p in stockpile["products"]}
    except Exception as e:
        print(f"⚠️ stockpile_map build failed: {e}")
        stockpile_map = {}
    
    for i, p in enumerate(json_products):
        resolved = p.get("resolved_details", p)
        
        raw_name = p.get("name", "")
        clean_name = re.sub(r'\s+', ' ', raw_name).strip()
        clean_name = re.sub(r'<br\s*/?>', ' ', clean_name, flags=re.IGNORECASE)
        
        item_id = p.get("id") or f"stockpile_{i + 1}"
        
        # stockpile_mapからASIN・rakuten_url・yahoo_url・image_urlを取得してマージ
        mapped_p = stockpile_map.get(raw_name) or stockpile_map.get(clean_name) or {}
        
        # 1. Amazonリンク：ASINがあれば必ずhttps://www.amazon.co.jp/dp/{ASIN}?tag=mikkestyle-22を使う
        asin = mapped_p.get("asin") or ""
        amazon_url = f"https://www.amazon.co.jp/dp/{asin}?tag=mikkestyle-22" if asin else ""
        
        # 2. 楽天リンク：resolved_details内のrakuten_urlを優先
        rakuten_url = mapped_p.get("resolved_details", {}).get("rakuten_url") or mapped_p.get("rakuten_url") or ""
        rakuten_url = clean_rakuten_url(rakuten_url)
        
        # 3. 商品画像・アイキャッチ：stockpile_data.jsonのimage_urlを使う
        image_url = mapped_p.get("image_url") or ""
        
        # Yahooリンク（バリューコマース用）
        yahoo_url = mapped_p.get("resolved_details", {}).get("yahoo_url") or mapped_p.get("yahoo_url") or ""
        yahoo_url = clean_yahoo_url(yahoo_url, clean_name)
        
        resolved_details = mapped_p.get("resolved_details", {})
        products.append({
            "id": item_id,
            "name": clean_name,
            "image_url": image_url,
            "amazon_url": amazon_url,
            "rakuten_url": rakuten_url,
            "yahoo_url": yahoo_url,
            "amazon_price": str(resolved_details.get("amazon_price", resolved.get("amazon_price", "なし"))),
            "rakuten_price": str(resolved_details.get("rakuten_price", resolved.get("rakuten_price", "なし"))),
            "yahoo_price": "なし",
            "category": category,
            "facts": p.get("facts", []),
            "recommended_for": p.get("recommended_for", []),
            "rating": mapped_p.get("rating") or ""
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
        if not validate():
            return False
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

    # 整合性チェック: ローカル一時データが指定された記事タイトルと一致しているか
    stockpile_path = os.path.join(script_dir, "stockpile_data.json")
    if os.path.exists(stockpile_path):
        try:
            with open(stockpile_path, 'r', encoding='utf-8') as sf:
                stock_data = json.load(sf)
                stock_cat = stock_data.get("category", "")
                norm_title = article_title.lower()
                norm_cat = stock_cat.lower()
                words = [w for w in re.split(r'[^a-zA-Z0-9\u3040-\u309f\u30a0-\u30ff\u4e00-\u9faf]+', norm_title) if len(w) >= 2]
                if stock_cat not in ["美容・スキンケア", "ガジェット", "家電", "暮らし", "ファッション"] and words and not any(w in norm_cat for w in words):
                    print(f"❌ 整合性エラー: 指定タイトル '{article_title}' と stockpile_data.json のカテゴリ '{stock_cat}' が一致しません。")
                    print("👉 prepare_stockpile.py が正しい Notion ページIDで実行されているか確認してください。")
                    return False
        except Exception as e:
            print(f"⚠️ stockpile_data.json の整合性チェックをスキップ (ロードエラー: {e})")

    draft_title = data.get("meta", {}).get("title", "")
    if draft_title:
        norm_title = article_title.lower()
        norm_draft = draft_title.lower()
        # 漢字、カタカナ、英数字、ひらがな（ノイズ語を除く）に分解
        raw_words = re.findall(r'[\u4e00-\u9faf]+|[\u30a0-\u30ff]+|[a-zA-Z0-9]+|[\u3040-\u309f]+', norm_title)
        noise_words = {"の", "おすすめ", "人気", "ランキング", "比較", "選び方", "用"}
        words = [w for w in raw_words if len(w) >= 2 and w not in noise_words]
        if words and not any(w in norm_draft for w in words):
            print(f"⚠️ 警告: 指定タイトル '{article_title}' と article_draft.json のメタタイトル '{draft_title}' に共通の主要単語が見つかりません。")
            print("👉 整合性を確認した上で処理を続行します。")
    
    output_title = data.get("meta", {}).get("title") or article_title.replace("2024", "2026")
    slug = slug or slugify(output_title, category, publish_date)

    duplicate_slug = check_recent_duplicate_topic(slug)
    if duplicate_slug:
        print(f"❌ 重複コンテンツ検知: '{slug}' は直近21日以内に公開済みの '{duplicate_slug}' と同じ商品カテゴリです。")
        print("👉 キーワードカニバリゼーション防止のため、この記事の公開を中止します。別の商品カテゴリを選定してください。")
        return False

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
        f'coverImage: "/eyecatch/{slug}.png"\n'
        f'excerpt: "{data.get("meta", {}).get("excerpt", "")}"\n'
        f'publishDate: "{publish_date}"\n'
        f'category: "{category}"\n'
        f'---\n\n'
        f'{intro_text}\n\n'
    )

    markdown += f"## ✅ 選び方のポイント\n<ul>" + "".join([f"<li>{p}</li>" for p in data.get("ui", {}).get("points", [])]) + "</ul>\n\n"

    def clean_brand_and_noise(name):
        n = re.sub(r'[\s\u3000\(\)\{\}\[\]【】\|｜\-\_\~・]', '', name).lower()
        # 主要ブランド名のノイズを除去
        brands = [
            "花王ニベア花王", "ニベア花王", "花王キュレル", "花王", "資生堂", "コーセーコスメポート", "コーセー", 
            "ロート製薬メンソレータム", "ロート製薬", "日本ロート製薬", "メンソレータム", "カネボウ化粧品", "カネボウ",
            "オルビス", "ファンケル", "アテニア", "ちふれ化粧品", "ちふれ", "セザンヌ化粧品", "セザンヌ", "常盤薬品工業", 
            "近江兄弟社メンターム", "近江兄弟社", "メンターム", "レイス", "シービック", "多田", "プレミアアンチエイジング", 
            "ランクアップ", "コスメデコルテ", "アルビオン", "キールズ", "アンドビー", "ラロッシュポゼ", "エトヴォス", 
            "シュウウエムラ", "dhc", "ルルルン", "dr.ルルルン", "ettusais", "エテュセ", "takami", "タカミ", "torriden", "トリデン",
            "イミュ", "ナチュリエ", "naturie"
        ]
        for b in brands:
            n = n.replace(b, "")
        # その他のノイズ語尾の除去
        noises = ["無香料", "医薬部外品", "薬用", "人気", "定番", "おすすめ", "コラーゲン", "セラミド", "リップケア", "リップクリーム", "リップバーム"]
        for ns in noises:
            n = n.replace(ns, "")
        return n

    for i, p in enumerate(data.get("products", [])):
        p_clean = clean_brand_and_noise(p['name'])
        notion_p = None
        for x in products:
            x_clean = clean_brand_and_noise(x['name'])
            # コア部分の相互包含チェック、または長さが十分なら部分一致
            if p_clean in x_clean or x_clean in p_clean or (len(p_clean) >= 4 and p_clean[:4] in x_clean) or (len(x_clean) >= 4 and x_clean[:4] in p_clean):
                notion_p = x
                break
        prod_name = re.sub(r'<br\s*/?>', ' ', p['name'], flags=re.IGNORECASE)
        display_name = truncate_product_name(prod_name)
        
        markdown += f"### 👑 第{i+1}位: {display_name}\n"
        
        rating = notion_p.get("rating") if notion_p else ""
        if rating:
            try:
                rating_val = float(rating)
                star_count = round(rating_val)
                star_count = max(0, min(5, star_count))
                stars = "★" * star_count + "☆" * (5 - star_count)
                markdown += f"[総合評価: {rating} / 5.0 {stars}]\n\n"
            except ValueError:
                markdown += f"[総合評価: {rating}]\n\n"
        
        if notion_p and notion_p['image_url']: 
            markdown += f"IMAGE: {notion_p['image_url']}\n"
        
        if notion_p:
            for platform in ['amazon', 'rakuten']:
                price = notion_p.get(f'{platform}_price')
                if price and price != "なし": markdown += f"{platform.upper()}_PRICE: {price}\n"
            for platform, key in [('amazon', 'asin'), ('rakuten', 'rakuten')]:
                url = notion_p.get(f'{platform}_url')
                if url: markdown += f"{key.upper()}: {url}\n"
        
        formatted_desc = p.get('description', '').replace('\\n', '\n\n')
        markdown += f"{formatted_desc}\n\n"
        
        markdown += f"[AMAZON_LINK_HERE] [RAKUTEN_LINK_HERE]\n\n"
        
        pros = p.get("analysis", {}).get("pros", [])
        cons = p.get("analysis", {}).get("cons", [])
        markdown += ":::pro\n" + "\n".join([f"{item}" for item in pros]) + "\n:::\n"
        markdown += ":::con\n" + "\n".join([f"{item}" for item in cons]) + "\n:::\n\n"
        
        markdown += f"👤 **こんな人におすすめ！**\n"
        markdown += "\n".join([f"- {item}" for item in p.get("analysis", {}).get("recommended_for", [])]) + "\n\n"
    
    comparison_table = "## 📊 比較表\n\n| 順位 | 商品名 | 価格 | 特徴 |\n| :---: | :--- | :---: | :--- |\n"
    for idx, p in enumerate(data.get("products", [])):
        prod_name = re.sub(r'<br\s*/?>', ' ', p['name'], flags=re.IGNORECASE)
        name_short = truncate_product_name(prod_name)
        p_name_clean = re.sub(r'[\s\u3000]', '', p['name']).lower()
        notion_p = None
        for x in products:
            x_name_clean = re.sub(r'[\s\u3000]', '', x['name']).lower()
            if x_name_clean in p_name_clean or p_name_clean in x_name_clean:
                notion_p = x
                break
        price = "なし"
        if notion_p:
            amazon_p = notion_p.get("amazon_price")
            rakuten_p = notion_p.get("rakuten_price")
            if amazon_p and amazon_p != "none" and amazon_p != "なし":
                price = amazon_p
            elif rakuten_p and rakuten_p != "none" and rakuten_p != "なし":
                price = rakuten_p
        if price and price != "なし":
            price_formatted = f"¥{int(price):,}" if price.isdigit() else price
        else:
            price_formatted = "ー"
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
        faq_items = [
            ("Q. 購入後の保証期間はどのくらいですか？", "A. 一般的なメーカー製品では、購入日から1年間の動作保証がついているものがほとんどです。購入時の領収書や保証書は大切に保管してください。"),
            ("Q. 日常のお手入れで気をつけるべき点は何ですか？", "A. 湿気やほこりがたまると火災や故障の原因になります。定期的に電源プラグを抜き、乾いた柔らかい布で本体の汚れを拭き取ってください。"),
            ("Q. 電気代はどのくらいかかりますか？", "A. LED製品は非常に省エネ設計です。例えば消費電力10Wのライトを1日10時間点灯した場合、1ヶ月の電気代は約90円程度と極めてリーズナブルです。")
        ]
        for q, a in faq_items:
            faq_section += f"### {q}\n{a}\n\n"
        
    markdown += faq_section + "\n"

    markdown += f"## 💬 まとめ\n"
    markdown += f"{data.get('content', {}).get('summary', '')}\n\n"
    markdown += f'<p class="pr-disclosure">{PR_DISCLOSURE}</p>\n'

    path = f"src/content/articles/{slug}.md"
    with open(path, 'w', encoding='utf-8') as f: f.write(markdown)
    
    image_urls = []
    for p in data.get("products", []):
        p_clean = clean_brand_and_noise(p['name'])
        for x in products:
            x_clean = clean_brand_and_noise(x['name'])
            if p_clean in x_clean or x_clean in p_clean or (len(p_clean) >= 4 and p_clean[:4] in x_clean) or (len(x_clean) >= 4 and x_clean[:4] in p_clean):
                if x.get('image_url'):
                    image_urls.append(x['image_url'])
                break
    generate_eyecatch_html(slug, output_title, category, image_urls, get_seasonal_catch_copy(category))
    take_eyecatch_screenshot(slug)
    
    # Pinterest用縦長画像の生成
    generate_pinterest_eyecatch_html(slug, output_title, category, image_urls, get_seasonal_catch_copy(category))
    take_pinterest_eyecatch_screenshot(slug)
    
    # Pinterestに自動投稿
    try:
        import sys
        sys.path.append(os.path.dirname(os.path.abspath(__file__)))
        from pinterest_auto_post import post_article_by_slug
        print(f"Sharing new article '{slug}' on Pinterest...")
        post_article_by_slug(slug)
    except Exception as e:
        print(f"[WARN] Failed to post to Pinterest: {e}")

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
