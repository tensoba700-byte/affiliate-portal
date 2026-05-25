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
    text = re.sub(r'[^\w\s-]', '', text).strip().lower()
    text = re.sub(r'[-\s]+', '-', text)
    jst = datetime.timezone(datetime.timedelta(hours=9))
    date_prefix = datetime.datetime.now(jst).strftime("%Y%m%d")
    return f"{date_prefix}-{text}"

def get_dispersed_publish_date() -> str:
    jst = datetime.timezone(datetime.timedelta(hours=9))
    today = datetime.datetime.now(jst).date()
    
    articles_dir = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "src", "content", "articles"
    )
    if not os.path.exists(articles_dir):
        return today.strftime("%Y-%m-%d")
        
    latest_date = today
    for fn in os.listdir(articles_dir):
        if not fn.endswith(".md") or fn == "GENERATION_RULES.md":
            continue
        try:
            with open(os.path.join(articles_dir, fn), 'r', encoding='utf-8') as f:
                content = f.read()
                m = re.search(r'publishDate:\s*["\']?(\d{4}-\d{2}-\d{2})["\']?', content)
                if m:
                    p_date = datetime.datetime.strptime(m.group(1), "%Y-%m-%d").date()
                    if p_date > latest_date:
                        latest_date = p_date
        except Exception:
            pass
            
    # If the latest article in the repo is already today or in the future, we schedule it for the day after that!
    if latest_date >= today:
        target_date = latest_date + datetime.timedelta(days=1)
    else:
        target_date = today
        
    return target_date.strftime("%Y-%m-%d")

def is_valid_product_details(details) -> bool:
    # Amazon check: must be a product page
    amz = details.get("amazon_url", "")
    if not amz or not ("/dp/" in amz or "/gp/" in amz):
        return False
        
    # Rakuten check: must be a specific item page
    rak = details.get("rakuten_url", "")
    if not rak or "item.rakuten.co.jp" not in rak:
        return False
        
    # Yahoo check: must be a specific store/product page
    yah = details.get("yahoo_url", "")
    if not yah or not ("store.shopping.yahoo.co.jp" in yah or "shopping.yahoo.co.jp/product" in yah):
        return False
        
    return True

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
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/120.0.0.0"
    }
    try:
        res = requests.get(url, headers=headers, timeout=15)
        if res.status_code != 200:
            return ""
        html = res.text
        html = re.sub(r'<script.*?</script>', '', html, flags=re.DOTALL | re.IGNORECASE)
        html = re.sub(r'<style.*?</style>', '', html, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r'<[^>]+>', ' ', html)
        text = re.sub(r'\s+', ' ', text).strip()
        return text[:25000]
    except Exception:
        return ""

def take_eyecatch_screenshot(slug: str) -> bool:
    node_bin = "node"
    script = "scripts/generate-eyecatch.js"
    try:
        result = subprocess.run(
            [node_bin, script, slug],
            capture_output=True, text=True, timeout=90
        )
        return result.returncode == 0
    except Exception:
        return False

# 高精度な商品検索APIクエリ
def fetch_product_details(query: str, jan_code: str = ""):
    details = {
        "image_url": "",
        "amazon_price": "なし",
        "rakuten_price": "なし",
        "yahoo_price": "なし",
        "rakuten_url": "",
        "yahoo_url": "",
        "amazon_url": ""
    }
    
    clean_query = re.sub(r'[\(（\[［].*?[\)）\]］]', ' ', query)
    noise_words = ["P&Gジャパン", "P&G", "資生堂", "カネボウ", "ロート製薬", "花王", "コーセー", "ポーラ", "ロレアル", "ラロッシュポゼ", "アルビオン", "ヤーマン", "アネッサ", "イハダ", "クレ・ド・ポー", "クラシエ", "ちふれ", "オルビス", "ファンケル"]
    for nw in noise_words:
        clean_query = re.sub(rf'\b{nw}\b', '', clean_query, flags=re.IGNORECASE)
        
    clean_query = re.sub(r'\s+', ' ', clean_query).strip()
    words = clean_query.split()
    fallback_query = " ".join(words[:3]) if len(words) > 3 else clean_query

    # JANコードが数字だけで8桁か13桁であるか厳しくチェック（重複・文字化けASIN混入を防ぐ）
    is_valid_jan = bool(jan_code and re.fullmatch(r'^\d{8}$|^\d{13}$', jan_code.strip()))

    # 検索優先度クエリリストの構築
    search_queries = []
    if is_valid_jan:
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
                        details["yahoo_price"] = str(hit.get("price", ""))
                        details["yahoo_url"] = hit.get("url", "")
                        img_url = hit.get("image", {}).get("medium") or ""
                        if img_url and "/i/g/" in img_url: img_url = img_url.replace("/i/g/", "/i/l/")
                        details["image_url"] = img_url
                        break
            except Exception: continue
            
    # 2. Rakuten Enterprise API
    rakuten_app_id = os.getenv("RAKUTEN_APP_ID")
    rakuten_access_key = os.getenv("RAKUTEN_ACCESS_KEY")
    rakuten_affiliate_id = os.getenv("RAKUTEN_AFFILIATE_ID")
    if rakuten_app_id and rakuten_access_key:
        for q in search_queries:
            try:
                params = {"format": "json", "keyword": q, "applicationId": rakuten_app_id, "accessKey": rakuten_access_key, "affiliateId": rakuten_affiliate_id, "hits": 1}
                res = requests.get("https://openapi.rakuten.co.jp/ichibams/api/IchibaItem/Search/20220601", params=params, timeout=10)
                if res.status_code == 200:
                    items = res.json().get("Items", [])
                    if items:
                        item = items[0].get("Item", {})
                        details["rakuten_price"] = str(item.get("itemPrice", ""))
                        details["rakuten_url"] = item.get("affiliateUrl") or item.get("itemUrl") or ""
                        img_url = item.get("mediumImageUrls", [{}])[0].get("imageUrl") or ""
                        if img_url: details["image_url"] = re.sub(r'\?_ex=\d+x\d+', '?_ex=640x640', img_url)
                        break
            except Exception: continue

    # 3. Amazon ASIN Scraping
    browser_h = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"}
    amazon_tag = os.getenv("AMAZON_ASSOCIATE_TAG", "mikkestyle-22")
    for q in search_queries:
        try:
            res = requests.get(f"https://www.amazon.co.jp/s?k={urllib.parse.quote(q)}", headers=browser_h, timeout=15)
            for m in re.finditer(r'data-asin="([A-Z0-9]{10})"', res.text):
                asin = m.group(1)
                block = res.text[m.start():m.start() + 3000]
                if not any(x in block.lower() for x in ["sponsored", "スポンサー"]):
                    details["amazon_url"] = f"https://www.amazon.co.jp/dp/{asin}?tag={amazon_tag}"
                    break
            if details["amazon_url"]: break
        except Exception: continue

    if not details["image_url"]: details["image_url"] = "https://images.unsplash.com/photo-1527443224154-c4a3942d3acf?w=500"
    return details

def generate_eyecatch_html(slug: str, title: str, category: str, image_urls: list) -> str:
    imgs_html = "".join([f'<div class="pw"><img src="{url}" class="pi" /></div>' for url in image_urls[:6]])
    html = f'<!DOCTYPE html><html><body><div class="g">{imgs_html}</div><div class="to"><h1>{title}</h1></div></body></html>'
    path = f"public/eyecatch/{slug}.html"
    with open(path, 'w', encoding='utf-8') as f: f.write(html)
    return path

def generate_with_retry(client, model_name, prompt, config=None, max_retries=3):
    for attempt in range(max_retries):
        try:
            return client.models.generate_content(model=model_name, contents=prompt, config=config)
        except Exception:
            time.sleep(15)
    return None

def search_competitor_url(keyword: str) -> str:
    """
    指定されたキーワードでGoogle検索を行い、最も情報量が豊富で
    信頼性の高いおすすめ・比較記事（my-best.comなど）のURLを1つ見つけて返します。
    ハルシネーションによる「無関係なURL」の選出を防ぐため、二重の検証ステップを挟みます。
    """
    if not client:
        print("❌ GEMINI_API_KEY が設定されていないため、検索を実行できません。")
        return ""

    print(f"🔍 キーワード 「{keyword}」 に関連する競合比較サイトをGoogle検索中...")
    prompt = (
        f"「{keyword} おすすめ 比較」でGoogle検索を行い、その結果から最も情報量が豊富で"
        f"信頼できる比較記事・レビューサイト（my-best.comや専門紹介メディアなど）の【実際のURL】と【その記事のタイトル】を上位から最大3つ教えてください。\n"
        f"存在しない嘘のURL（ハルシネーション）をでっち上げないよう、実際に検索結果に存在する本物のURLのみを出力してください。\n"
        f"出力形式は必ず以下のように、各候補を1つずつ記述してください（余計な説明は省く）：\n"
        f"TITLE: [記事のタイトル]\n"
        f"URL: [本物のURL]\n"
    )

    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
            config=types.GenerateContentConfig(
                tools=[types.Tool(google_search=types.GoogleSearch())],
                temperature=0.0
            )
        )
        text = response.text.strip()
        print(f"🔍 検索 Grounding の生応答:\n{text}\n")
        
        candidates = []
        matches = re.findall(r'TITLE:\s*(.*?)\nURL:\s*(https?://[^\s`"\'<>\(\)\[\]]+)', text, re.IGNORECASE)
        if not matches:
            urls = re.findall(r'https?://[^\s`"\'<>\(\)\[\]]+', text)
            for u in urls:
                if "my-best.com" in u or "kakaku.com" in u or "360life.jp" in u:
                    candidates.append({"title": keyword, "url": u})
        else:
            for m in matches:
                candidates.append({"title": m[0].strip(), "url": m[1].strip()})
        
        if not candidates:
            print("⚠️ 検索結果から候補URLを抽出できませんでした。")
            return ""
            
        for cand in candidates:
            cand_title = cand["title"]
            cand_url = cand["url"]
            
            print(f"🧐 候補の検証中: 「{cand_title}」 ({cand_url})")
            
            verification_prompt = (
                f"あなたはアフィリエイト記事の編集長です。以下の選定された競合URLとタイトルが、"
                f"指定されたキーワード「{keyword}」に関するおすすめ・比較・レビュー記事であるかどうかを厳密に判定してください。\n"
                f"タイトル: {cand_title}\n"
                f"URL: {cand_url}\n"
                f"キーワード: {keyword}\n\n"
                f"もし、テーマが完全に一致し、そのキーワードのおすすめ記事である場合は「YES」、"
                f"全く関係のない別の商品（例: スマートウォッチとマグカップなど）や無関係なURLである場合は「NO」と答えてください。\n"
                f"余計な理由は一切含めず、「YES」または「NO」のいずれか1文字のみを出力してください。"
            )
            
            ver_res = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=verification_prompt,
                config=types.GenerateContentConfig(temperature=0.0)
            )
            
            decision = ver_res.text.strip().upper()
            print(f"👉 判定結果: {decision}")
            if "YES" in decision:
                print(f"✨ 厳密検証をクリアした競合URL: {cand_url}")
                return cand_url
            else:
                print(f"⚠️ テーマ不一致またはハルシネーションのため棄却しました: {cand_url}")
                
        print("⚠️ すべての候補URLが検証をクリアできませんでした。")
        return ""
    except Exception as e:
        print(f"❌ Google Search Grounding または検証中にエラーが発生しました: {e}")
        return ""

def fetch_knowledge_by_search(keyword: str) -> str:
    """
    スクレイピングが失敗した場合に、Google Search Grounding を使って
    そのキーワードに対する代表的なおすすめ商品6選の情報をGeminiに調査させ、
    競合サイトの代わりとなるテキストを生成します。
    """
    if not client:
        return ""
    print(f"💡 スクレイピングの代わりに Google Search Grounding で「{keyword}」のおすすめ商品を直接調査中...")
    prompt = (
        f"「{keyword} おすすめ」でGoogle検索を行い、現在日本国内で非常に人気が高く、"
        f"おすすめされる代表的な商品を6つ特定してください。\n"
        f"それぞれの商品の名称、メーカー名、主な特徴、および詳細な説明、そして「どんな人におすすめか」の情報を詳細にまとめ、"
        f"1つのテキストとして出力してください。このテキスト is 後続の商品特定・記事執筆プロセスで競合サイトのデータとして使用されます。"
    )
    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
            config=types.GenerateContentConfig(
                tools=[types.Tool(google_search=types.GoogleSearch())],
                temperature=0.2
            )
        )
        return response.text.strip()
    except Exception as e:
        print(f"❌ フォールバック調査中にエラーが発生しました: {e}")
        return ""

def generate_from_competitor(input_target: str, default_category: str = "ガジェット"):
    if not client:
        print("❌ GEMINI_API_KEY が設定されていません。")
        return False

    # URLかキーワードかを判別
    is_input_url = input_target.startswith("http://") or input_target.startswith("https://")
    
    competitor_url = ""
    keyword = ""
    competitor_text = ""
    
    if is_input_url:
        competitor_url = input_target
        print(f"🔍 競合サイトを直接解析中: {competitor_url}")
        competitor_text = fetch_url_text(competitor_url)
    else:
        keyword = input_target
        print(f"🔑 検索キーワードを受信: 「{keyword}」")
        # Google検索で競合URLを探索
        competitor_url = search_competitor_url(keyword)
        
        if competitor_url:
            competitor_text = fetch_url_text(competitor_url)
            
        if not competitor_text:
            print("⚠️  選定した競合URLからのスクレイピングに失敗しました。フォールバック調査を実行します。")
            competitor_text = fetch_knowledge_by_search(keyword)

    if not competitor_text:
        print("❌ 競合サイトの解析および検索調査のすべてに失敗しました。サンプルデータを使用します。")
        competitor_text = "【デスクツアー】在宅ワークが劇的に快適になる！おすすめの便利ガジェット6選をご紹介します。1. エルゴトロン LX モニターアーム（ディスプレイを浮かせてデスク広々） 2. BenQ ScreenBar Halo（目に優しいモニターライト） 3. HHKB Professional HYBRID Type-S（最高の打鍵感のキーボード） 4. Logicool MX Master 3S（多機能・静音マウス） 5. 山善 電動昇降デスク（姿勢改善・健康） 6. Anker 737 Charger（超急速充電）"

    rules_text = load_generation_rules()
    title_quality_rules = load_title_quality_rules()

    print("🧠 [第1ステージ] Geminiで紹介商品を特定中...")
    
    meta_prompt = f"""あなたはプロのWebライターとして、提供されたライバルサイトのテキストデータを分析し、
そこで紹介されている「上位おすすめ商品」を【最大10件】特定してください。
また、記事全体のタイトル、カテゴリ、要約、導入文、選び方のポイント、まとめ文を作成してください。
商品の詳細説明文はこのステージでは記述せず、商品名と推奨ターゲットのみを返してください。

{title_quality_rules}

【抽出・生成にあたっての厳格な指示】
1. **商品名とターゲットの完全一致**: 各商品の特徴や紹介文を競合テキストから精査し、その商品に固有の「こんな人におすすめ」を正確に設定してください。他の商品の特徴が混ざったり、シャッフルされたりすることは絶対に避けてください。
2. **JANコードの抽出と補完**: 
   - 提供された競合テキスト内にJANコード（13桁または8桁の数字）が記載されている場合は、それを完璧に抽出して `jan_code` に格納してください。
   - 事前知識から該当する商品の正確なJANコードがわかる場合は、必ずそれを調べて補完してください。
   - JANコードがどうしても不明な場合、または数字8桁・13桁以外の場合は、必ず空文字 `""` にしてください。AmazonのASINやアルファベットを含む文字列は絶対に `jan_code` に入れないでください。
3. **カテゴリ名の厳格制限**: `category` は必ず『美容・スキンケア』『ガジェット』『インテリア』『生活雑貨』『便利グッズ』の5つのいずれかに完全に一致させて分類してください。これら以外のカテゴリ名は絶対に使用しないでください。
4. **情緒的かつSEOに配慮した英語スラッグの生成**: `english_slug` フィールドに、商品のテーマを簡潔に表す英語/半角英数字（例：`smartwatch-comparison`, `sunscreen-recommendations`, `kitchen-gadgets`）を生成してください。スペースは使わず、ハイフンで繋いでください。
5. **タイトルの絶対禁止ワード**: 以下の単語をタイトルに含めることは絶対に禁止します：
   - 誇張：「劇的」「激変」「驚き」「絶対」「マジ」「ヤバい」「神」「最強」「殿堂入り」
   - テンプレ：「おすすめ〇選」「人気〇選」「ランキング」「必見」「まとめ」「比較してみた」「徹底比較」「最新」「2024」「2026」
   - 一人称/二人称：「私が」「あなたも」
   - 感嘆符（！）の連続使用
   - タイトルは必ず `[情緒的なメインタイトル]【[キーワードを含むサブタイトル]】` の【基本形】で出力してください。
6. **根拠なき検証アピールの禁止 (薬機法・景表法対策)**: 導入文（intro）やまとめ文（summary）において、「〇〇商品を徹底検証」「専門機器でのデータ検証」「皮膚科医による共同開発」など、客観的根拠のない嘘の検証アピールは絶対に書かないでください。「編集部が厳選した」「読者に寄り添うおすすめの選択肢」といった、誠実で法律的にも安全なトーンで執筆してください。
7. **おこげペルソナ・一人称の排除**: 信頼性の高的かつ優しいブランドボイスで、親しみやすくも知的なトーンで記述してください。「おこげ」や「私」などの一人称は使用しないでください。

提供された競合テキスト:
---
{competitor_text}
---

【第1ステージ JSONスキーマ】
以下のJSONフォーマットで完全に記述し、JSON以外の余計なテキストは一切含めずに出力してください。
{{
  "title": "読者を惹きつける、上記品質基準を完全に満たした魅力的な記事タイトル（禁止ワードを完全に排除し、基本形を守ること）",
  "category": "美容・スキンケア/ガジェット/インテリア/生活雑貨/便利グッズ のいずれか",
  "english_slug": "半角英数字とハイフンのみの英語スラッグ（例：smartwatch-comparison）",
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
      "jan_code": "JANコード（数字8桁または13桁のみ。見つからない場合は空文字）",
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
    
    # 5つの主要カテゴリのいずれかでない場合は「ガジェット」にフォールバック
    valid_categories = ["美容・スキンケア", "ガジェット", "インテリア", "生活雑貨", "便利グッズ"]
    if category not in valid_categories:
        category = default_category if default_category in valid_categories else "ガジェット"
        
    english_slug = data.get("english_slug", "product-recommendations")
    slug = slugify(english_slug)
    
    print(f"📝 記事メタ取得完了: {title} (Slug: {slug})")
    
    PR_DISCLOSURE = "※本記事はアフィリエイト広告を含みます。"
    intro_text = clean_variable_names(data.get("intro", "").replace(PR_DISCLOSURE, "").strip())

    markdown = (
        f'--- \n'
        f'title: "{title}"\n'
        f'coverImage: ""\n'
        f'excerpt: "{data.get("excerpt", "")}"\n'
        f'publishDate: "{get_dispersed_publish_date()}"\n'
        f'category: "{category}"\n'
        f'---\n\n'
        f'{intro_text}\n\n'
        f'## ✅ 選び方のポイント\n<ul>'
        + "".join([f"<li>{p}</li>" for p in data.get("points", [])])
        + "</ul>\n\n"
    )

    image_urls = []
    
    print("🧠 [第2ステージ] 各商品の超詳細説明文（1000文字以上）をループ生成中...")
    
    valid_products_count = 0
    used_asins = set()
    used_rakuten_urls = set()
    used_yahoo_urls = set()
    used_images = set()
    
    # 10件の候補から条件を満たす6つの商品を選定する
    for candidate_idx, p in enumerate(data.get("products", [])):
        if valid_products_count >= 6:
            break
            
        p_name = p.get("name", "")
        jan_code = p.get("jan_code", "")
        display_name = truncate_product_name(p_name)
        
        print(f"🧐 候補商品 [{candidate_idx+1}/{len(data.get('products', []))}] {p_name} (JAN: {jan_code}) の検証中...")
        
        # APIで画像と価格、URLを検索
        api_data = fetch_product_details(p_name, jan_code)
        
        # 1. 有効な個別商品ページURLが3つのプラットフォームすべてで取得できたか？
        if not is_valid_product_details(api_data):
            print(f"   ❌ 特定の商品ページURLが取得できませんでした（検索結果URLを含むため除外）")
            continue
            
        # AmazonのASINをURLから抽出
        asin_match = re.search(r'/dp/([A-Z0-9]{10})|/gp/product/([A-Z0-9]{10})', api_data["amazon_url"])
        asin = asin_match.group(1) or asin_match.group(2) if asin_match else ""
        
        # 2. 重複チェック（同一記事内に同じASIN、楽天URL、YahooURL、画像URLがないか）
        if asin in used_asins:
            print(f"   ❌ 重複検知: ASIN {asin} は既に他の商品で使用されています。")
            continue
        if api_data["rakuten_url"] in used_rakuten_urls:
            print(f"   ❌ 重複検知: 楽天URL は既に他の商品で使用されています。")
            continue
        if api_data["yahoo_url"] in used_yahoo_urls:
            print(f"   ❌ 重複検知: YahooURL は既に他の商品で使用されています。")
            continue
        if api_data["image_url"] in used_images:
            print(f"   ❌ 重複検知: 画像URL は既に他の商品で使用されています。")
            continue
            
        # 重複がなければ、この商品を採用！
        used_asins.add(asin)
        used_rakuten_urls.add(api_data["rakuten_url"])
        used_yahoo_urls.add(api_data["yahoo_url"])
        used_images.add(api_data["image_url"])
        
        valid_products_count += 1
        print(f"   ✅ 検証クリア！ {p_name} を第 {valid_products_count} 位として採用します。")
        
        if valid_products_count > 1:
            print("   ⏳ 429回避のため、12秒間スリープします...")
            time.sleep(12)
            
        # 順位に応じたスコアの決定 (1位は4.8〜4.9、最下位は4.3〜4.4のように綺麗に分散させる)
        assigned_score = round(4.95 - (valid_products_count * 0.1), 2)
        
        desc_prompt = f"""あなたは「みっけ！」アフィリエイトブログの専属プロライターです。
このセクションは、記事全体の「{p_name}」という個別の商品紹介部分にそのまま挿入されます。
以下のルールに厳格に従い、高品質で読者に信頼される製品紹介文を執筆してください。

【厳格ルール】
1. **自己紹介や読者への語りかけは絶対に禁止**です。「こんにちは」「みっけ！専属ライターの〇〇です」などの始まり方は絶対にしないでください。「おこげ」「私」といった一人称や個人の体験談を装った記述もすべて禁止です。
2. **商品説明の圧縮**: 説明文は**5〜8段落（合計500〜700文字程度）**に凝縮し、余計なコピペ感のあるお決まりの美辞麗句（「肌にのせた瞬間に〜」「未来の肌への投資」など）を完全に排除してください。
3. **段落分け**: 各段落は**1〜2文程度**とし、段落間には空行（\n\n）を入れてスマホで最も読みやすい構成にしてください。また、文章が長く繋がらないように配慮してください。
4. **絵文字の制限**: 絵文字は**1商品につき1〜2個まで**に厳しく制限してください。過剰な装飾は避けてください。
5. **禁止ワード**: 「マジで」「ヤバい」「神アイテム」「最高」「究極」などの誇張・下品な表現は厳禁です。
6. **総合評価スコア**: この商品の総合評価点数として、必ず `{assigned_score}` を使用し、行頭に必ず `[総合評価: {assigned_score}]` と出力してください。
7. **メリット・デメリットの追加**: 
   製品説明の後に、必ずメリットとデメリットのセクションを以下の形式で出力してください。
   読者から信頼されるために、デメリット（con）は必ず具体的かつ誠実に書いてください。
   ※注意: デメリット（con）に「高価」「高い」「価格帯が高め」「価格がネック」などの価格に関する否定表現は絶対に書かないでください（GENERATION_RULES.mdのルールに従ってください）。代わりに、機能面や仕様面での具体的な懸念点（例：『防水性能が生活防水レベル』『設定にスマートフォンが必須』など）を記述してください。
   :::pro
   メリット1つめ（1行で簡潔に）
   メリット2つめ（1行で簡潔に）
   :::
   :::con
   デメリット1つめ（1行で簡潔に）
   デメリット2つめ（1行で簡潔に）
   :::

そのまま記事に挿入できるプレーンテキストとして出力してください（JSONやマークダウンのコードブロックで囲わないでください）。
"""
        desc_res = generate_with_retry(
            client,
            'gemini-2.5-flash',
            desc_prompt,
            config=types.GenerateContentConfig(temperature=0.6)
        )
        
        desc_text = desc_res.text.strip() if desc_res else f"[総合評価: {assigned_score}]\n\n詳細な製品紹介を準備中です。"
        desc = clean_variable_names(desc_text)
        
        image_urls.append(api_data["image_url"])
        
        escaped_name = urllib.parse.quote(p_name)
        amazon_url = api_data["amazon_url"]
        rakuten_url = api_data["rakuten_url"]
        yahoo_url = api_data["yahoo_url"]
        
        # 👑 第1位: 商品名 の順位ヘッダーを付与
        markdown += f"### 👑 第{valid_products_count}位: {display_name}\n"
        markdown += f"IMAGE: {api_data['image_url']}\n"
        markdown += f"AMAZON_PRICE: {api_data['amazon_price']}\n"
        markdown += f"RAKUTEN_PRICE: {api_data['rakuten_price']}\n"
        markdown += f"YAHOO_PRICE: {api_data['yahoo_price']}\n"
        markdown += f"ASIN: {amazon_url}\n"
        markdown += f"RAKUTEN: {rakuten_url}\n"
        markdown += f"YAHOO: {yahoo_url}\n\n"
        
        # 総合評価スコア、説明文、メリット・デメリットの結合
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
        print("使用法: python3 scripts/generate_from_competitor.py [競合サイトのURL または 検索キーワード]")
        sys.exit(1)
        
    target = sys.argv[1]
    slug = generate_from_competitor(target)
    if slug:
        print(f"\n🎉 成功！新しい記事が作成されました：\n/articles/{slug}")
    else:
        sys.exit(1)
