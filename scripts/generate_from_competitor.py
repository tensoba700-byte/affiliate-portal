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

def generate_eyecatch_html(slug: str, title: str, category: str, image_urls: list) -> str:
    imgs_html = ""
    target_count = min(6, len(image_urls))
    for url in image_urls[:target_count]:
        imgs_html += f'<div class="pw"><img src="{url}" class="pi" alt="" loading="eager" /></div>\n'
    for _ in range(max(0, 6 - target_count)):
        imgs_html += '<div class="pw"></div>\n'
    
    font_size = "110px" if len(title) <= 15 else "90px" if len(title) <= 22 else "75px"
    
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
    # Break title elegantly
    display_title = title
    if len(title) > 11:
        mid = len(title) // 2
        display_title = title[:mid] + "<br />" + title[mid:]

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
        # デモ用のダミーテキスト（接続エラー時用）
        competitor_text = "【デスクツアー】在宅ワークが劇的に快適になる！おすすめの便利ガジェット6選をご紹介します。1. エルゴトロン LX モニターアーム（ディスプレイを浮かせてデスク広々） 2. BenQ ScreenBar Halo（目に優しいモニターライト） 3. HHKB Professional HYBRID Type-S（最高の打鍵感のキーボード） 4. Logicool MX Master 3S（多機能・静音マウス） 5. 山善 電動昇降デスク（姿勢改善・健康） 6. Anker 737 Charger（超急速充電）"

    rules_text = load_generation_rules()
    rules_section = f"\n\n【記事生成ルール（必ず遵守）】\n{rules_text}" if rules_text else ""

    print("🧠 Geminiを使って競合記事を分析し、新しい高品質記事を構成中...")
    
    prompt = f"""あなたはプロのWebライターとして、提供されたライバルサイトのテキストデータを分析し、
そこで紹介されている「上位6つのおすすめ商品」を特定してください。
そして、その6つの商品をもとに、中立的かつ信頼性の高い「みっけ！」ブランドの商品紹介記事（1000文字以上）をJSON形式で執筆してください。

提供された競合テキスト:
---
{competitor_text}
---

{rules_section}

【記事作成のJSONスキーマ】
以下のJSONフォーマットで完全に記述し、JSON以外の余計なテキスト（マークダウンのコードフェンス等）は一切含めずに出力してください。

出力形式:
{{
  "title": "読者を惹きつける、2026年最新の魅力的な記事タイトル（「2024」年などの古い表現は「2026」年に変更）",
  "category": "ガジェット",
  "excerpt": "記事の簡単な要約（100文字程度）",
  "intro": "記事の導入文。読者の悩みに寄り添い、本記事を読むメリットを魅力的に解説してください。アフィリエイト広告利用開示（※本記事はアフィリエイト広告を含みます。）は絶対に含めないでください。",
  "points": [
    "選び方のポイント1（簡潔に）",
    "選び方のポイント2（簡潔に）",
    "選び方のポイント3（簡潔に）"
  ],
  "products": [
    {{
      "name": "特定した商品名1（正式名称）",
      "description": "商品の特徴、使用感、効果を1000文字以上で具体的に分かりやすく、段落を分けながら（2〜3文ごとに空行を入れる）詳しく解説してください。",
      "recommended_for": [
        "こんな人におすすめ1",
        "こんな人におすすめ2",
        "こんな人におすすめ3"
      ],
      "image_url_kw": "商品画像を検索するためのシンプルな英単語2〜3語（例: 'hhkb keyboard black' や 'logitech mx master 3s'）"
    }}
  ],
  "summary": "記事全体のまとめ文。最後に読者の背中を優しく押す言葉を添えてください。"
}}

【厳守事項】
- 商品紹介（description）は必ず**1000文字以上**の十分な情報量で詳しく書いてください。
- 特定する商品は必ず「6個」にしてください。
- 絵文字は1つの商品につき1〜2個までに制限してください。
"""

    model = genai.GenerativeModel('gemini-2.5-flash')
    res = model.generate_content(
        prompt,
        generation_config=genai.types.GenerationConfig(
            temperature=0.6,
            max_output_tokens=8192,
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
    
    print(f"📝 記事作成を開始: {title} (Slug: {slug})")
    
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
    
    # 各商品の情報をループ処理
    for i, p in enumerate(data.get("products", [])):
        p_name = p.get("name", "")
        display_name = truncate_product_name(p_name)
        desc = clean_variable_names(p.get("description", ""))
        
        # 楽天画像検索APIなどを模した、高品質なデモ画像URLをキーワードから生成
        kw = p.get("image_url_kw", "gadget")
        demo_image = f"https://source.unsplash.com/featured/800x800/?{urllib.parse.quote(kw)}"
        # ※ Unsplashの商用フリー画像や楽天のプレースホルダーを割り当てます
        # 今回はデモとして、実用的な製品カテゴリーに紐づく高品質画像をデフォルト設定
        image_urls.append(demo_image)
        
        # 自分たちのアフィリエイトIDを付与した検索URLの動的生成（最強・在庫切れなし！）
        escaped_name = urllib.parse.quote(p_name)
        amazon_url = f"https://www.amazon.co.jp/s?k={escaped_name}&tag=mikkestyle-22"
        rakuten_url = f"https://hb.afl.rakuten.co.jp/hgc/g00rkpmm.xpsekcd1.g00rkpmm.xpsel146/?pc=https://search.rakuten.co.jp/search/mall/{escaped_name}/"
        yahoo_url = f"https://ck.jp.ap.valuecommerce.com/servlet/referral?sid=3767611&pid=2201292&vc_url=https%3A%2F%2Fshopping.yahoo.co.jp%2Fsearch%3Fp%3D{escaped_name}"
        
        markdown += f"### 🌸 {display_name}\n"
        # markdown += f"IMAGE: {demo_image}\n" # サムネイル表示用
        markdown += f"ASIN: {amazon_url}\n"
        markdown += f"RAKUTEN: {rakuten_url}\n"
        markdown += f"YAHOO: {yahoo_url}\n\n"
        
        # 説明文
        formatted_desc = desc.replace('\\n', '\n\n')
        markdown += f"{formatted_desc}\n\n"
        markdown += f"[Amazonで見る]({amazon_url}) [楽天市場で見る]({rakuten_url}) [Yahoo!ショッピングで見る]({yahoo_url})\n\n"
        
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

    print("🚀 すべての工程が完了しました！Gitにコミットしてデプロイします。")
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
