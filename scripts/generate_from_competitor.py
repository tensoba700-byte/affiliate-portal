import os
import re
import sys
import json
import datetime
import urllib.parse
import requests
import subprocess
import google.generativeai as genai
from dotenv import load_dotenv

# Env読み込み
load_dotenv(".env.local")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

# 記事生成ルール読み込み
def load_generation_rules() -> str:
    rules_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "GENERATION_RULES.md"
    )
    if os.path.exists(rules_path):
        with open(rules_path, 'r', encoding='utf-8') as f:
            return f.read()
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
def fetch_product_details(query: str):
    """
    Rakuten & Yahoo Shopping APIを使って正確な画像、価格、およびアフィリエイトURLを取得する。
    """
    details = {
        "image_url": "",
        "amazon_price": "価格を見る",
        "rakuten_price": "価格を見る",
        "yahoo_price": "価格を見る",
        "rakuten_url": "",
        "yahoo_url": ""
    }
    
    # 1. Yahoo Shopping API V3
    yahoo_app_id = os.getenv("YAHOO_SHOPPING_APP_ID")
    if yahoo_app_id:
        try:
            url = f"https://shopping.yahooapis.jp/ShoppingWebService/V3/itemSearch?appid={yahoo_app_id}&query={urllib.parse.quote(query)}&results=1"
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
                    details["image_url"] = hit.get("image", {}).get("medium") or hit.get("image", {}).get("small") or ""
                    print(f"   [Yahoo API] 取得成功: {query} -> 価格: {details['yahoo_price']}")
        except Exception as e:
            print(f"   ⚠️ Yahoo API エラー: {e}")
            
    # 2. Rakuten Item Search API
    rakuten_app_id = os.getenv("RAKUTEN_APP_ID")
    rakuten_affiliate_id = os.getenv("RAKUTEN_AFFILIATE_ID")
    if rakuten_app_id:
        try:
            url = f"https://app.rakuten.co.jp/services/api/IchibaItem/Search/20220601?applicationId={rakuten_app_id}&keyword={urllib.parse.quote(query)}&hits=1"
            if rakuten_affiliate_id:
                url += f"&affiliateId={rakuten_affiliate_id}"
            res = requests.get(url, timeout=10)
            if res.status_code == 200:
                data = res.json()
                items = data.get("Items", [])
                if items:
                    item = items[0].get("Item", {})
                    price_val = item.get("itemPrice")
                    if price_val:
                        details["rakuten_price"] = str(price_val)
                    details["rakuten_url"] = item.get("affiliateUrl") or item.get("itemUrl") or ""
                    if not details["image_url"]:
                        med_imgs = item.get("mediumImageUrls", [])
                        if med_imgs:
                            details["image_url"] = med_imgs[0].get("imageUrl") or ""
                    print(f"   [Rakuten API] 取得成功: {query} -> 価格: {details['rakuten_price']}")
        except Exception as e:
            print(f"   ⚠️ Rakuten API エラー: {e}")

    # 画像取得失敗時の高品質なUnsplashプレースホルダー
    if not details["image_url"]:
        details["image_url"] = f"https://images.unsplash.com/photo-1527443224154-c4a3942d3acf?w=500"
        
    return details

# アイキャッチ画像の改行ルール（絶対にはみ出さない）
def format_eyecatch_title(title: str) -> str:
    cleaned = title.replace("【2026年版】", "").replace("【2024年版】", "").strip()
    if len(cleaned) <= 11:
        return cleaned
    
    lines = []
    current = ""
    for char in cleaned:
        current += char
        # 11〜13文字付近で、助詞などの区切りが良い部分で改行
        if len(current) >= 11 and char in ["の", "で", "に", "は", "が", "を", "し", "と", "、", "！", "？", " ", "　", "「", "」"]:
            lines.append(current)
            current = ""
        elif len(current) >= 13:  # 13文字強制改行
            lines.append(current)
            current = ""
    if current:
        lines.append(current)
    
    return "<br />".join(lines)

def generate_eyecatch_html(slug: str, title: str, category: str, image_urls: list) -> str:
    imgs_html = ""
    target_count = min(6, len(image_urls))
    for url in image_urls[:target_count]:
        imgs_html += f'<div class="pw"><img src="{url}" class="pi" alt="" loading="eager" /></div>\n'
    for _ in range(max(0, 6 - target_count)):
        imgs_html += '<div class="pw"></div>\n'
    
    display_title = format_eyecatch_title(title)
    line_count = display_title.count("<br />") + 1
    
    # 行数に基づいて文字フォントサイズを動的に調整（絶対に画面はみ出しを防ぐ！）
    if line_count >= 4:
        font_size = "45px"
    elif line_count == 3:
        font_size = "55px"
    else:
        font_size = "70px"
        
    css = f"""@import url('https://fonts.googleapis.com/css2?family=M+PLUS+Rounded+1c:wght@800;900&display=swap');
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
html, body {{ width: 1200px; height: 630px; overflow: hidden; background: #fff; }}
body {{ font-family: 'M PLUS Rounded 1c', sans-serif; display: flex; align-items: center; justify-content: center; position: relative; }}
.g {{ display: grid; grid-template-columns: repeat(3, 1fr); grid-template-rows: repeat(2, 1fr); width: 1200px; height: 630px; padding: 20px; gap: 20px; }}
.pw {{ width: 100%; height: 100%; display: flex; align-items: center; justify-content: center; background: #fdfdfd; border-radius: 20px; border: 1px solid #f0f0f0; }}
.pi {{ max-width: 320px; max-height: 240px; object-fit: contain; mix-blend-mode: multiply; }}
.to {{ position: absolute; inset: 0; display: flex; align-items: center; justify-content: center; z-index: 100; pointer-events: none; }}
.ti {{ font-size: {font_size}; font-weight: 900; color: #000; line-height: 1.35; text-align: center; padding: 30px 50px; background: rgba(255, 255, 255, 0.85); border-radius: 30px; box-shadow: 0 10px 40px rgba(0,0,0,0.15); border: 2px solid rgba(255,255,255,0.9); word-break: keep-all; max-width: 950px; }}
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

# 競合サイトの分析とアフィリエイト記事生成
def generate_from_competitor(competitor_url: str, default_category: str = "ガジェット"):
    print(f"🔍 競合サイトを解析中: {competitor_url}")
    competitor_text = fetch_url_text(competitor_url)
    
    if not competitor_text:
        print("❌ 競合サイトからテキスト情報を抽出できませんでした。サンプルデータを使用します。")
        competitor_text = "【デスクツアー】在宅ワークが劇的に快適になる！おすすめの便利ガジェット6選をご紹介します。1. エルゴトロン LX モニターアーム（ディスプレイを浮かせてデスク広々） 2. BenQ ScreenBar Halo（目に優しいモニターライト） 3. HHKB Professional HYBRID Type-S（最高の打鍵感のキーボード） 4. Logicool MX Master 3S（多機能・静音マウス） 5. 山善 電動昇降デスク（姿勢改善・健康） 6. Anker 737 Charger（超急速充電）"

    rules_text = load_generation_rules()

    print("🧠 [第1ステージ] Geminiで紹介商品を特定中...")
    
    meta_prompt = f"""あなたはプロのWebライターとして、提供されたライバルサイトのテキストデータを分析し、
そこで紹介されている「上位6つのおすすめ商品」を特定してください。
また、記事全体のタイトル、カテゴリ、要約、導入文、選び方のポイント、まとめ文を作成してください。
商品の詳細説明文はこのステージでは記述せず、商品名と推奨ターゲットのみを返してください。

提供された競合テキスト:
---
{competitor_text}
---

【第1ステージ JSONスキーマ】
以下のJSONフォーマットで完全に記述し、JSON以外の余計なテキストは一切含めずに出力してください。
{{
  "title": "読者を惹きつける、2026年最新の魅力的な記事タイトル（「2024」年などの古い表現は「2026」年に変更）",
  "category": "ガジェット",
  "excerpt": "記事の簡単な要約（100文字程度）",
  "intro": "記事の導入文。読者の悩みに寄り添い、本記事を読むメリットを魅力的に解説してください。",
  "points": [
    "選び方のポイント1",
    "選び方のポイント2",
    "選び方のポイント3"
  ],
  "products": [
    {{
      "name": "特定した商品名（メーカー名＋正確な商品名。余分なSEOキーワードは除外）",
      "recommended_for": [
        "こんな人におすすめ1",
        "こんな人におすすめ2",
        "こんな人におすすめ3"
      ]
    }}
  ],
  "summary": "記事全体のまとめ文。最後に読者の背中を優しく押す言葉を添えてください。"
}}
"""

    model = genai.GenerativeModel('models/gemini-2.5-flash')
    res = model.generate_content(
        meta_prompt,
        generation_config=genai.types.GenerationConfig(
            temperature=0.4,
            response_mime_type="application/json"
        )
    )
    
    if not res:
        print("❌ Geminiからの応答がありませんでした。")
        return False
        
    try:
        data = json.loads(res.text)
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
        f'publishDate: "{datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).isoformat()}"\n'
        f'category: "{category}"\n'
        f'---\n\n'
        f'{intro_text}\n\n'
        f'## ✅ 選び方のポイント\n<ul>'
        + "".join([f"<li>{p}</li>" for p in data.get("points", [])])
        + "</ul>\n\n"
    )

    image_urls = []
    
    # [第2ステージ] 各商品の詳細説明文をループで個別に執筆（Geminiのトークン制限切れによるJSON破損を100%防ぐ！）
    print("🧠 [第2ステージ] 各商品の超詳細説明文（1000文字以上）をループ生成中...")
    
    for i, p in enumerate(data.get("products", [])):
        p_name = p.get("name", "")
        display_name = truncate_product_name(p_name)
        
        print(f"🛍️  [{i+1}/6] {p_name} の詳細説明文（1000文字以上）を生成中...")
        
        desc_prompt = f"""あなたは「みっけ！」アフィリエイトブログの専属プロライターです。
商品『{p_name}』について、中立的で信頼性が高く、読者の購買意欲をそそる素晴らしい紹介文を執筆してください。

【執筆ルール】
- 紹介文は必ず**1000文字以上**の圧倒的なボリュームで執筆してください。
- 特徴、メリット、実際の使用感、類似品との違いなどを多角的に解説してください。
- スマートフォンで読みやすいよう、**2〜3文ごとに空行（段落改行）**を必ず入れてください。
- 絵文字は全体で1〜2個程度に抑え、過剰な装飾は避けてください。
- トーンは優しく親しみやすくも、客観的でプロフェッショナルなものにしてください。

【生成用の禁止ワード】
「マジで」「ヤバい」「神アイテム」「最高」「究極」などの誇張・下品な表現は厳禁です。

そのまま記事に挿入できるプレーンテキストとして出力してください（JSONやマークダウンのコードブロックで囲わないでください）。
"""

        desc_res = model.generate_content(
            desc_prompt,
            generation_config=genai.types.GenerationConfig(temperature=0.6)
        )
        
        desc_text = desc_res.text.strip() if desc_res else "詳細な製品紹介を準備中です。"
        desc = clean_variable_names(desc_text)
        
        print(f"🔍 APIで画像と価格を検索中: {p_name} ...")
        # Rakuten & Yahoo APIを使って正確なデータ（画像・価格・URL）を検索！
        api_data = fetch_product_details(p_name)
        
        image_urls.append(api_data["image_url"])
        
        escaped_name = urllib.parse.quote(p_name)
        amazon_url = f"https://www.amazon.co.jp/s?k={escaped_name}&tag=mikkestyle-22"
        rakuten_url = api_data["rakuten_url"] or f"https://hb.afl.rakuten.co.jp/hgc/g00rkpmm.xpsekcd1.g00rkpmm.xpsel146/?pc=https://search.rakuten.co.jp/search/mall/{escaped_name}/"
        yahoo_url = api_data["yahoo_url"] or f"https://ck.jp.ap.valuecommerce.com/servlet/referral?sid=3767611&pid=2201292&vc_url=https%3A%2F%2Fshopping.yahoo.co.jp%2Fsearch%3Fp%3D{escaped_name}"
        
        # Next.jsパーサー（src/lib/api.ts）に100%適合するヘッダー構成！
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
        
        # Next.jsパーサーがボタンに置換する最強のプレースホルダー！
        markdown += f"[AMAZON_LINK_HERE] [RAKUTEN_LINK_HERE] [YAHOO_LINK_HERE]\n\n"
        
        # 推奨項目
        markdown += f"👤 **こんな人におすすめ！**\n"
        markdown += "\n".join([f"- {item}" for item in p.get("recommended_for", [])]) + "\n\n"

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
        print("使用法: python3 scripts/generate_from_competitor.py [競合サイト of URL]")
        sys.exit(1)
        
    url = sys.argv[1]
    slug = generate_from_competitor(url)
    if slug:
        print(f"\n🎉 成功！新しい記事が作成されました：\n/articles/{slug}")
    else:
        sys.exit(1)
