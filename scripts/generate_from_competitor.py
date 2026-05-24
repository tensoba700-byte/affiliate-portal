import os
import time
import re
import sys
import json
import datetime
import urllib.parse
import requests
import subprocess
from google import genai
from google.genai import types
from dotenv import load_dotenv

# Env読み込み
load_dotenv(".env.local")
# For local development compatibility
load_dotenv(os.path.expanduser("~/.gemini/antigravity/scratch/discord-bot/.env"))

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# 新SDKのClientを初期化
client = None
if GEMINI_API_KEY:
    client = genai.Client(api_key=GEMINI_API_KEY)

# 記事生成ルール（GENERATION_RULES.md）の読み込み
def load_generation_rules() -> str:
    rules_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "GENERATION_RULES.md"
    )
    if os.path.exists(rules_path):
        with open(rules_path, 'r', encoding='utf-8') as f:
            return f.read()
    return ""

# タイトル品質基準（product_selection_prompt.txt）の動的読み込み
def load_title_quality_rules() -> str:
    prompt_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "product_selection_prompt.txt"
    )
    if os.path.exists(prompt_path):
        with open(prompt_path, 'r', encoding='utf-8') as f:
            content = f.read()
            # 「# ■ 記事タイトル品質基準（最重要）」から「# ■ 実行手順」までのセクションを抽出
            m = re.search(r'(# ■ 記事タイトル品質基準.*?)(?=# ■ 実行手順|$)', content, re.DOTALL)
            if m:
                return m.group(1).strip()
    return ""

def slugify(text: str) -> str:
    text = text.replace("2024", "2026")
    text = re.sub(r'[^\w\s-]', '', text).strip().lower()
    text = re.sub(r'[-\s]+', '-', text)
    jst = datetime.timezone(datetime.timedelta(hours=9))
    date_prefix = datetime.datetime.now(jst).strftime("%Y%m%d")
    return f"{date_prefix}-{text[:30]}"

def clean_variable_names(text: str) -> str:
    patterns = [
        r'\b(YAHOO_PRICE|RAKUTEN_PRICE|AMAZON_PRICE)\b\s*[:：]?\s*\S*',
        r'\b(YAHOO|RAKUTEN|AMAZON|ASIN)\s*[:：]\s*\S*',
    ]
    for pattern in patterns:
        text = re.sub(pattern, '', text, flags=re.IGNORECASE)
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text

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

# ライバルサイトのHTMLテキスト取得
def fetch_url_text(url: str) -> str:
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    try:
        res = requests.get(url, headers=headers, timeout=15)
        if res.status_code != 200:
            print(f"⚠️  URLの取得に失敗しました (ステータスコード: {res.status_code})")
            return ""
        html = res.text
        html = re.sub(r'<script.*?</script>', '', html, flags=re.DOTALL | re.IGNORECASE)
        html = re.sub(r'<style.*?</style>', '', html, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r'<[^>]+>', ' ', html)
        text = re.sub(r'\s+', ' ', text).strip()
        return text[:25000]  # 25,000文字制限
    except Exception as e:
        print(f"❌ URL取得エラー: {e}")
        return ""

def take_eyecatch_screenshot(slug: str) -> bool:
    node_bin = "node"
    script = "scripts/generate-eyecatch.js"
    try:
        result = subprocess.run(
            [node_bin, script, slug],
            capture_output=True, text=True, timeout=90
        )
        if result.returncode != 0:
            print(f"⚠️  eyecatch stderr: {result.stderr[:500]}")
        return result.returncode == 0
    except Exception as e:
        print(f"❌ Eyecatch screenshot failed: {e}")
        return False

# 高精度な商品検索APIクエリ
def fetch_product_details(query: str, jan_code: str = ""):
    """
    Rakuten OpenAPI & Yahoo Shopping API & Amazon Scrapingを使って
    正確な画像、価格、および個別の商品アフィリエイトURLを取得する。
    """
    details = {
        "image_url": "",
        "amazon_price": "なし",
        "rakuten_price": "なし",
        "yahoo_price": "なし",
        "rakuten_url": "",
        "yahoo_url": "",
        "amazon_url": ""
    }
    
    # 検索精度向上のためにクエリをクレンジング
    clean_query = query
    clean_query = re.sub(r'[\(（\[［].*?[\)）\]］]', ' ', clean_query)
    
    # ブランド名や社名のノイズワードリスト
    noise_words = [
        "P&Gジャパン", "P&Gプレステージ", "P&G", "資生堂", "カネボウ化粧品", "カネボウ", "KANEBO",
        "ロート製薬", "再春館製薬所", "再春館製薬", "花王", "コーセー", "KOSE", "ポーラ", "POLA",
        "日本ロレアル", "ロレアル", "L'Oreal", "ラロッシュポゼ", "LA ROCHE POSAY", "ラ ロッシュ ポゼ",
        "アルビオン", "ALBION", "ヤーマン", "YA-MAN", "アネッサ", "ANESSA", "イハダ", "IHADA",
        "クレ・ド・ポー ボーテ", "クレ・ド・ポー", "クレドポーボーテ", "クレドポー", "Cle de Peau Beaute",
        "クラシエ", "Kracie", "ちふれ", "CHIFURE", "オルビス", "ORBIS", "ファンケル", "FANCL"
    ]
    
    for nw in noise_words:
        clean_query = re.sub(rf'\b{nw}\b', '', clean_query, flags=re.IGNORECASE)
        clean_query = clean_query.replace(nw, "")
        
    clean_query = re.sub(r'\s+', ' ', clean_query).strip()
    
    words = clean_query.split()
    fallback_query = " ".join(words[:3]) if len(words) > 3 else clean_query

    # 検索優先度クエリリストの構築
    search_queries = []
    if jan_code and jan_code.strip():
        search_queries.append(jan_code.strip())
    search_queries.extend([clean_query, fallback_query])

    # 1. Yahoo Shopping API V3
    yahoo_app_id = os.getenv("YAHOO_SHOPPING_APP_ID")
    if yahoo_app_id:
        for q in search_queries:
            try:
                url = f"https://shopping.yahooapis.jp/ShoppingWebService/V3/itemSearch?appid={yahoo_app_id}&query={urllib.parse.quote(q)}&results=1"
                res = requests.get(url, timeout=10)
                if res.status_code == 200:
                    data = res.json()
                    hits = data.get("hits", [])
                    if hits:
                        hit = hits[0]
                        price_val = hit.get("price")
                        if price_val:
                            details["yahoo_price"] = str(price_val)
                        details["yahoo_url"] = hit.get("url", "")
                        
                        img_url = hit.get("image", {}).get("medium") or hit.get("image", {}).get("small") or ""
                        if img_url and "/i/g/" in img_url:
                            img_url = img_url.replace("/i/g/", "/i/l/")
                        details["image_url"] = img_url
                        
                        print(f"   [Yahoo API] 取得成功 (query: {q}) -> 価格: {details['yahoo_price']}")
                        break
            except Exception as e:
                print(f"   ⚠️ Yahoo API エラー (query: {q}): {e}")
            
    # 2. Rakuten Enterprise API
    rakuten_app_id = os.getenv("RAKUTEN_APP_ID")
    rakuten_access_key = os.getenv("RAKUTEN_ACCESS_KEY")
    rakuten_affiliate_id = os.getenv("RAKUTEN_AFFILIATE_ID")
    
    if rakuten_app_id and rakuten_access_key:
        rakuten_h = {
            "Referer": "https://www.mikke-style.com",
            "Origin": "https://www.mikke-style.com"
        }
        for q in search_queries:
            try:
                url = "https://openapi.rakuten.co.jp/ichibams/api/IchibaItem/Search/20220601"
                params = {
                    "format": "json",
                    "keyword": q,
                    "applicationId": rakuten_app_id,
                    "accessKey": rakuten_access_key,
                    "affiliateId": rakuten_affiliate_id,
                    "hits": 1
                }
                res = requests.get(url, params=params, headers=rakuten_h, timeout=10)
                if res.status_code == 200:
                    data = res.json()
                    items = data.get("Items", [])
                    if items:
                        item = items[0].get("Item", {})
                        price_val = item.get("itemPrice")
                        if price_val:
                            details["rakuten_price"] = str(price_val)
                        details["rakuten_url"] = item.get("affiliateUrl") or item.get("itemUrl") or ""
                        
                        med_imgs = item.get("mediumImageUrls", [])
                        large_imgs = item.get("largeImageUrls", [])
                        img_url = ""
                        if large_imgs:
                            img_url = large_imgs[0].get("imageUrl") or ""
                        elif med_imgs:
                            img_url = med_imgs[0].get("imageUrl") or ""
                        
                        if img_url:
                            img_url = re.sub(r'\?_ex=\d+x\d+', '?_ex=640x640', img_url)
                            
                        if not details["image_url"] or "unsplash.com" in details["image_url"]:
                            details["image_url"] = img_url
                            
                        print(f"   [Rakuten API] 取得成功 (query: {q}) -> 価格: {details['rakuten_price']}")
                        break
            except Exception as e:
                print(f"   ⚠️ Rakuten API エラー (query: {q}): {e}")

    # 3. Amazon ASIN Scraping
    browser_h = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept-Language": "ja,en;q=0.9"
    }
    # アソシエイトタグは公式タグの "mikkestyle-22" に完全統一
    amazon_tag = os.getenv("AMAZON_ASSOCIATE_TAG", "mikkestyle-22")
    for q in search_queries:
        try:
            search_url = f"https://www.amazon.co.jp/s?k={urllib.parse.quote(q)}&l=ja_JP"
            res = requests.get(search_url, headers=browser_h, timeout=15)
            asins = list(dict.fromkeys(re.findall(r'/dp/([A-Z0-9]{10})', res.text)))
            if asins:
                asin = asins[0]
                details["amazon_url"] = f"https://www.amazon.co.jp/dp/{asin}?tag={amazon_tag}"
                print(f"   [Amazon Scraper] ASIN取得成功 (query: {q}) -> ASIN: {asin}")
                break
        except Exception as e:
            print(f"   ⚠️ Amazon ASIN取得エラー (query: {q}): {e}")

    if not details["amazon_url"]:
        escaped_name = urllib.parse.quote(clean_query)
        details["amazon_url"] = f"https://www.amazon.co.jp/s?k={escaped_name}&tag={amazon_tag}"

    if not details["image_url"]:
        details["image_url"] = f"https://images.unsplash.com/photo-1527443224154-c4a3942d3acf?w=500"
        
    return details

# アイキャッチ画像の最新デザイン（白枠なし・影文字・日本語自動改行）
def extract_badge(title: str) -> str:
    m = re.search(r'(\d+)選', title)
    if m: return f"人気{m.group(1)}選"
    if '比較' in title: return '徹底比較'
    if 'ランキング' in title: return '人気ランキング'
    if 'おすすめ' in title: return 'おすすめ特集'
    return 'みっけ！厳選'

def format_eyecatch_title(title: str) -> str:
    cleaned = title.replace("【2026年版】", "").replace("【2024年版】", "").strip()
    if len(cleaned) <= 11:
        return cleaned
    
    separators = ["の", "で", "に", "は", "が", "を", "！", "？", "：", "、", " ", "　"]
    mid = len(cleaned) // 2
    for offset in [0, 1, -1, 2, -2, 3, -3]:
        idx = mid + offset
        if 0 < idx < len(cleaned) - 1 and cleaned[idx] in separators:
            return cleaned[:idx+1] + "<br />" + cleaned[idx+1:]
            
    return cleaned[:mid] + "<br />" + cleaned[mid:]

def generate_eyecatch_html(slug: str, title: str, category: str, image_urls: list) -> str:
    imgs_html = ""
    target_count = min(6, len(image_urls))
    for url in image_urls[:target_count]:
        imgs_html += f'<div class="pw"><img src="{url}" class="pi" alt="" loading="eager" /></div>\n'
    for _ in range(max(0, 6 - target_count)):
        imgs_html += '<div class="pw"></div>\n'
    
    display_title = format_eyecatch_title(title)
    line_count = display_title.count("<br />") + 1
    
    # 行数に応じたフォントサイズ動的スケーリング（はみ出しを完全ガード）
    if line_count >= 4:
        font_size = "70px"
    elif line_count == 3:
        font_size = "85px"
    else:
        font_size = "105px"
        
    css = f"""@import url('https://fonts.googleapis.com/css2?family=M+PLUS+Rounded+1c:wght@800;900&display=swap');
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
html, body {{ width: 1200px; height: 630px; overflow: hidden; background: #fff; }}
body {{ font-family: 'M PLUS Rounded 1c', sans-serif; display: flex; align-items: center; justify-content: center; position: relative; }}
.g {{ display: grid; grid-template-columns: repeat(3, 1fr); grid-template-rows: repeat(2, 1fr); width: 1200px; height: 630px; padding: 20px; gap: 20px; }}
.pw {{ width: 100%; height: 100%; display: flex; align-items: center; justify-content: center; }}
.pi {{ max-width: 360px; max-height: 280px; object-fit: contain; mix-blend-mode: multiply; }}
.to {{ position: absolute; inset: 0; display: flex; align-items: center; justify-content: center; z-index: 100; pointer-events: none; }}
.ti {{ font-size: {font_size}; font-weight: 900; color: #000; line-height: 1.25; text-align: center; padding: 0 60px; text-shadow: 0 0 20px #fff, 0 0 20px #fff, 0 0 20px #fff; word-break: keep-all; }}
"""

    html = f"""<!DOCTYPE html>
<html lang="ja"><head><meta charset="UTF-8" /><style>{css}</style></head><body>
<div class="g">{imgs_html}</div>
<div class="to"><h1 class="ti">{display_title}</h1></div>
</body></html>"""
    path = f"public/eyecatch/{slug}.html"
    with open(path, 'w', encoding='utf-8') as f:
        f.write(html)
    return path

# 新SDKに対応したリトライ機能付きAPI呼び出しロジック
def generate_with_retry(client, model_name, prompt, config=None, max_retries=5, initial_delay=15):
    delay = initial_delay
    current_model_name = model_name
    
    # 2.5安定版、Lite版、2.0安定版をフォールバックに設定
    fallback_candidates = [
        "gemini-2.5-flash",
        "gemini-2.5-flash-lite",
        "gemini-2.0-flash-lite",
        "gemini-2.0-flash",
    ]
    fallback_index = 0
    
    for attempt in range(max_retries):
        try:
            return client.models.generate_content(
                model=current_model_name,
                contents=prompt,
                config=config
            )
        except Exception as e:
            err_msg = str(e)
            print(f"   ⚠️ Gemini APIエラー (試行 {attempt+1}/{max_retries}): {err_msg}")
            
            # クォータ制限（1日あたりの20回制限など）に達した場合、自動フォールバックを実行
            if "Quota exceeded" in err_msg and fallback_index < len(fallback_candidates):
                next_model_name = fallback_candidates[fallback_index]
                if next_model_name == current_model_name:
                    fallback_index += 1
                    if fallback_index < len(fallback_candidates):
                        next_model_name = fallback_candidates[fallback_index]
                    else:
                        next_model_name = None
                
                if next_model_name:
                    fallback_index += 1
                    print(f"   🔄 クォータ制限を検知。モデルを {next_model_name} に変更して再試行します...")
                    current_model_name = next_model_name
                    continue
            
            if attempt == max_retries - 1:
                raise e
            print(f"   ⏳ {delay}秒後に再試行します...")
            time.sleep(delay)
            delay *= 1.5

# 競合サイトの分析とアフィリエイト記事生成
def generate_from_competitor(competitor_url: str, default_category: str = "ガジェット"):
    if not client:
        print("❌ GEMINI_API_KEY が設定されていません。")
        return False

    print(f"🔍 競合サイトを解析中: {competitor_url}")
    competitor_text = fetch_url_text(competitor_url)
    
    if not competitor_text:
        print("❌ 競合サイトからテキスト情報を抽出できませんでした。サンプルデータを使用します。")
        competitor_text = "【デスクツアー】在宅ワークが劇的に快適になる！おすすめの便利ガジェット6選をご紹介します。1. エルゴトロン LX モニターアーム（ディスプレイを浮かせてデスク広々） 2. BenQ ScreenBar Halo（目に優しいモニターライト） 3. HHKB Professional HYBRID Type-S（最高の打鍵感のキーボード） 4. Logicool MX Master 3S（多機能・静音マウス） 5. 山善 電動昇降デスク（姿勢改善・健康） 6. Anker 737 Charger（超急速充電）"

    rules_text = load_generation_rules()
    title_quality_rules = load_title_quality_rules()

    print("🧠 [第1ステージ] Geminiで紹介商品を特定中...")
    
    meta_prompt = f"""あなたはプロのWebライターとして、提供されたライバルサイトのテキストデータを分析し、
そこで紹介されている「上位6つのおすすめ商品」を特定してください。
また、記事全体のタイトル、カテゴリ、要約、導入文、選び方のポイント、まとめ文を作成してください。
商品の詳細説明文はこのステージでは記述せず、商品名と推奨ターゲットのみを返してください。

{title_quality_rules}

【抽出・生成にあたっての厳格な指示】
1. **商品名とターゲットの完全一致**: 各商品の特徴や紹介文を競合テキストから精査し、その商品に固有の「こんな人におすすめ」を正確に設定してください。他の商品の特徴（別の商品の機能など）が混ざったり、シャッフルされたりすることは絶対に避けてください。
2. **JANコードの抽出と補完**: 
   - 提供された競合テキスト内にJANコード（13桁または8桁の数字）が記載されている場合は、それを完璧に抽出して `jan_code` に格納してください。
   - 事前知識から該当する商品の正確なJANコードがわかる場合は、必ずそれを調べて補完してください。
   - JANコードがどうしても不明な場合のみ、空文字 `""` にしてください。
3. **おこげペルソナ・一人称の排除**: 信頼性の高い中立的かつ優しいブランドボイスで、親しみやすくも知的なトーンで記述してください。「おこげ」や「私」などの一人称は使用しないでください。

提供された競合テキスト:
---
{competitor_text}
---

【第1ステージ JSONスキーマ】
以下のJSONフォーマットで完全に記述し、JSON以外の余計なテキストは一切含めずに出力してください。
{{
  "title": "読者を惹きつける、上記品質基準を完全に満たした魅力的な記事タイトル（「2024」年などの古い表現は「2026」年に変更。必ず情緒タイトルと機能タイトルの【基本形】を使用すること）",
  "category": "カテゴリ名",
  "excerpt": "記事の簡単な要約（100文字程度）",
  "intro": "記事の導入文。読者の悩みに寄り添い、本記事を読むメリットを魅力的に解説してください。PR開示テキストは含めないでください。",
  "points": [
    "選び方のポイント1",
    "選び方のポイント2",
    "選び方のポイント3"
  ],
  "products": [
    {{
      "name": "特定した商品名（メーカー名＋正確な商品名。余分なSEOキーワードは除外）",
      "jan_code": "JANコード。見つからない場合は空文字",
      "recommended_for": [
        "この商品に完全に一致する、こんな人におすすめ1",
        "この商品に完全に一致する、こんな人におすすめ2",
        "この商品に完全に一致する、こんな人におすすめ3"
      ]
    }}
  ],
  "summary": "記事全体のまとめ文。最後に読者の背中を優しく押す言葉を添えてください。PR開示テキストは含めないでください。"
}}
"""

    # 新SDKの types.GenerateContentConfig クラスを使用
    config = types.GenerateContentConfig(
        temperature=0.4,
        response_mime_type="application/json"
    )
    res = generate_with_retry(
        client,
        'gemini-2.5-flash',
        meta_prompt,
        config=config
    )
    
    if not res:
        print("❌ Geminiからの応答がありませんでした。")
        return False
        
    try:
        text_to_parse = res.text.strip()
        if text_to_parse.startswith("```json"):
            text_to_parse = text_to_parse[7:]
        if text_to_parse.endswith("```"):
            text_to_parse = text_to_parse[:-3]
        text_to_parse = text_to_parse.strip()
        
        match = re.search(r'(\{.*\}).*', text_to_parse, re.DOTALL)
        if match:
            text_to_parse = match.group(1)
            
        try:
            data = json.loads(text_to_parse)
        except json.JSONDecodeError as jde:
            if "Extra data" in str(jde):
                pos = jde.pos
                data = json.loads(text_to_parse[:pos].strip())
            else:
                raise jde
    except Exception as e:
        print(f"❌ JSONデコードエラー: {e}\n生データ:\n{res.text}")
        return False

    title = data.get("title", "最新のおすすめアイテム").replace("2024", "2026")
    category = data.get("category", default_category)
    slug = slugify(title)
    
    print(f"📝 記事メタ取得完了: {title} (Slug: {slug})")
    
    PR_DISCLOSURE = "※本記事はアフィリエイト広告を含みます。"
    intro_text = clean_variable_names(data.get("intro", "").replace(PR_DISCLOSURE, "").strip())

    markdown = (
        f'--- \n'
        f'title: "{title}"\n'
        f'coverImage: ""\n'
        f'excerpt: "{data.get("excerpt", "")}"\n'
        f'publishDate: "{datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).strftime("%Y-%m-%d")}"\n'
        f'category: "{category}"\n'
        f'---\n\n'
        f'{intro_text}\n\n'
        f'## ✅ 選び方のポイント\n<ul>'
        + "".join([f"<li>{p}</li>" for p in data.get("points", [])])
        + "</ul>\n\n"
    )

    image_urls = []
    
    print("🧠 [第2ステージ] 各商品の超詳細説明文（1000文字以上）をループ生成中...")
    
    for i, p in enumerate(data.get("products", [])):
        if i > 0:
            print("⏳ 429回避のため、12秒間スリープします...")
            time.sleep(12)
        p_name = p.get("name", "")
        jan_code = p.get("jan_code", "")
        display_name = truncate_product_name(p_name)
        
        print(f"🛍️  [{i+1}/6] {p_name} (JAN: {jan_code}) の詳細説明文（1000文字以上）を生成中...")
        
        desc_prompt = f"""あなたは「みっけ！」アフィリエイトブログの専属プロライターです。
このセクションは、記事全体の「{p_name}」という個別の商品紹介部分にそのまま挿入されます。
したがって、以下の【禁止事項】を厳格に守り、純粋な商品解説文のみを執筆してください。

【禁止事項（極めて重要）】
- **自己紹介や読者への語りかけは絶対に禁止**です。「こんにちは」「みっけ！専属ライターの〇〇です」などの始まり方は絶対にしないでください。「おこげ」「私」といった一人称や個人の体験談を装った記述もすべて禁止です。
- **記事全体の導入文やまとめ文のような構成は禁止**です。最初から『{p_name}』の具体的な製品特徴や解説に直接入ってください。
- **個別商品紹介の締めくくりの挨拶や行動喚起は絶対に禁止**です。「ぜひ一度試してみてください」「〜をみっけてみませんか？✨」などの終わりの言葉や、まとめ段落は一切書かないでください。
- 商品紹介の終わりは、製品の特徴や魅力についての解説の途中で自然に終えてください。

【執筆ルール】
- 紹介文は必ず**1000文字以上**の圧倒的なボリュームで執筆してください。
- 特徴、メリット、実際の使用感、類似品との違いなどを多角的に解説してください。
- 各段落は**1〜2文程度**とし、段落間には空行（\n\n）を入れてスマホで最も読みやすい構成にしてください。また、文章が長く繋がらないように配慮してください。
- 絵文字は**1商品につき1〜2個まで**に制限してください。過剰な装飾は避けてください。
- トーンは優しく親しみやすくも、客観的でプロフェッショナルなものにしてください。

【生成用の禁止ワード】
「マジで」「ヤバい」「神アイテム」「最高」「究極」などの誇張・下品な表現は厳禁です。

そのまま記事に挿入できるプレーンテキストとして出力してください（JSONやマークダウンのコードブロックで囲わないでください）。
"""

        desc_res = generate_with_retry(
            client,
            'gemini-2.5-flash',
            desc_prompt,
            config=types.GenerateContentConfig(temperature=0.6)
        )
        
        desc_text = desc_res.text.strip() if desc_res else "詳細な製品紹介を準備中です。"
        desc = clean_variable_names(desc_text)
        
        print(f"🔍 APIで画像と価格を検索中: {p_name} (JAN: {jan_code}) ...")
        api_data = fetch_product_details(p_name, jan_code)
        
        image_urls.append(api_data["image_url"])
        
        escaped_name = urllib.parse.quote(p_name)
        amazon_url = api_data["amazon_url"]
        rakuten_url = api_data["rakuten_url"] or f"https://hb.afl.rakuten.co.jp/hgc/g00rkpmm.xpsekcd1.g00rkpmm.xpsel146/?pc=https://search.rakuten.co.jp/search/mall/{escaped_name}/"
        yahoo_url = api_data["yahoo_url"] or f"https://ck.jp.ap.valuecommerce.com/servlet/referral?sid=3767611&pid=2201292&vc_url=https%3A%2F%2Fshopping.yahoo.co.jp%2Fsearch%3Fp%3D{escaped_name}"
        
        # プレースホルダー残存バグを防ぐため、API取得に失敗した際の価格の初期化は "なし" で統一
        markdown += f"### 🌸 {display_name}\n"
        markdown += f"IMAGE: {api_data['image_url']}\n"
        markdown += f"AMAZON_PRICE: {api_data['amazon_price']}\n"
        markdown += f"RAKUTEN_PRICE: {api_data['rakuten_price']}\n"
        markdown += f"YAHOO_PRICE: {api_data['yahoo_price']}\n"
        markdown += f"ASIN: {amazon_url}\n"
        markdown += f"RAKUTEN: {rakuten_url}\n"
        markdown += f"YAHOO: {yahoo_url}\n\n"
        
        # 説明文
        formatted_desc = desc.replace('\\n', '\n\n')
        markdown += f"{formatted_desc}\n\n"
        
        markdown += f"[AMAZON_LINK_HERE] [RAKUTEN_LINK_HERE] [YAHOO_LINK_HERE]\n\n"
        
        markdown += f"👤 **こんな人におすすめ！**\n"
        markdown += "\n".join([f"- {item}" for item in p.get("recommended_for", [])]) + "\n\n"

    # PR表記は GENERATION_RULES.md に従って、## 💬 まとめ のすぐ下にのみ配置
    markdown += f"## 💬 まとめ\n{clean_variable_names(data.get('summary', ''))}\n\n"
    markdown += f'<p class="pr-disclosure">{PR_DISCLOSURE}</p>\n'

    # マークダウン書き出し
    path = f"src/content/articles/{slug}.md"
    with open(path, 'w', encoding='utf-8') as f:
        f.write(markdown)
    
    print(f"✅ 記事ファイルを生成しました: {path}")

    # アイキャッチ生成
    try:
        generate_eyecatch_html(slug, title, category, image_urls)
        take_eyecatch_screenshot(slug)
    except Exception as e:
        print(f"⚠️  アイキャッチ生成をスキップしました: {e}")

    print("🚀 すべての工程が完了しました！")
    return slug

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("使用法: python3 scripts/generate_from_competitor.py [競合サイトのURL]")
        sys.exit(1)
        
    url = sys.argv[1]
    slug = generate_from_competitor(url)
    if slug:
        print(f"\n🎉 成功！新しい記事が作成されました：\n/articles/{slug}")
    else:
        sys.exit(1)
