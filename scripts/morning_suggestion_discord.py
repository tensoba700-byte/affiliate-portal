import os
import datetime
import json
import random
import re
import time
import requests
import xml.etree.ElementTree as ET
from dotenv import load_dotenv

# Load credentials
load_dotenv("/Users/tsukika/Desktop/affiliate-portal/.env.local")
load_dotenv("/Users/tsukika/.gemini/antigravity/scratch/discord-bot/.env")

NOTION_API_KEY    = os.getenv("NOTION_API_KEY")
GROQ_API_KEY      = os.getenv("GROQ_API_KEY")
DISCORD_TOKEN     = os.getenv("DISCORD_TOKEN")
TARGET_CHANNEL_ID = os.getenv("TARGET_CHANNEL_ID")
RAKUTEN_APP_ID    = os.getenv("RAKUTEN_APP_ID")
RAKUTEN_ACCESS_KEY = os.getenv("RAKUTEN_ACCESS_KEY")

ARTICLE_MANAGE_DB_ID = "8511908442c74738b78dc62f6a7a49d9"

NOTION_HEADERS = {
    "Authorization": f"Bearer {NOTION_API_KEY}",
    "Notion-Version": "2022-06-28",
    "Content-Type": "application/json"
}

# ─────────────────────────────────────────
# トレンド収集
# ─────────────────────────────────────────

def fetch_google_trends():
    """Google トレンドの RSS から急上昇キーワードを取得する。"""
    headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}
    try:
        url = "https://trends.google.com/trends/trendingsearches/daily/rss?geo=JP"
        res = requests.get(url, headers=headers, timeout=10)
        if res.status_code == 200:
            root = ET.fromstring(res.content)
            titles = [item.find('title').text for item in root.findall('.//item')][:15]
            return titles
    except Exception as e:
        print(f"  ⚠️ Google Trends 取得失敗: {e}")
    return []

def fetch_rakuten_hot_ranking():
    """楽天リアルタイムランキングから上位商品名を取得する。"""
    params = {
        "applicationId": RAKUTEN_APP_ID,
        "accessKey":     RAKUTEN_ACCESS_KEY,
        "type":          "realtime",
        "formatVersion": 2
    }
    url = "https://openapi.rakuten.co.jp/ichibams/api/IchibaItem/Ranking/20170608"
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Referer": "https://www.mikke-style.com/",
        "Origin": "https://www.mikke-style.com/"
    }
    try:
        res = requests.get(url, params=params, headers=headers, timeout=10)
        if res.status_code == 200:
            items = res.json().get("Items", [])
            return [item.get("itemName", "")[:50] for item in items][:15]
    except Exception as e:
        print(f"  ⚠️ Rakuten Hot Ranking 取得失敗: {e}")
    return []

# YahooリアルタイムはAPI公開されていないため、上位2ソースを優先

# ─────────────────────────────────────────
# カテゴリ定義
# ─────────────────────────────────────────

MIKKE_CATEGORIES = [
    {"name": "美容・スキンケア", "genreId": "100533"},
    {"name": "ガジェット", "genreId": "215783"},
    {"name": "インテリア", "genreId": "100804"},
    {"name": "生活雑貨", "genreId": "558885"},
    {"name": "便利グッズ", "genreId": "101211"}
]

def get_daily_categories():
    base_date = datetime.date(2024, 1, 1)
    days = (datetime.date.today() - base_date).days
    morning_idx = days % len(MIKKE_CATEGORIES)
    night_idx = (days + 1) % len(MIKKE_CATEGORIES)
    return MIKKE_CATEGORIES[morning_idx], MIKKE_CATEGORIES[night_idx]

# ─────────────────────────────────────────
# 企画・キーワード生成 (Gemini/LLM)
# ─────────────────────────────────────────

def decide_theme_and_keywords(trends, category_name):
    """
    トレンド情報を元に、Geminiがそのカテゴリに合った具体的な商品ジャンルキーワードを生成する。
    """
    trend_text = "\n".join(f"- {t}" for t in trends)
    prompt = f"""現在のトレンドキーワード:
{trend_text}

上記トレンドや現在の季節（{datetime.date.today()}）を考慮し、「みっけ！」のカテゴリ【{category_name}】に合致する、
思わず欲しくなるような具体的でニッチな商品ジャンルのキーワードを3つ提案してください。

【条件】
- 「これ知らなかった！」「便利そう！」と思わせる、トレンド感や季節感のあるもの。
- 日用消耗品（スリッパ、はんこ、布団、洗剤、シャンプー、タオル、食品など）は絶対に除外すること。
- 商品名ではなく、「具体的な商品ジャンルや特徴を表す検索語句」にすること。
- 価格帯は 1,000円〜30,000円 を想定。

【出力形式（JSONのみ）】
{{
  "theme": "今回の記事テーマ",
  "keywords": ["検索キーワード1", "検索キーワード2", "検索キーワード3"]
}}
"""
    try:
        res = requests.post("https://api.groq.com/openai/v1/chat/completions", headers={
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json"
        }, json={
            "model": "llama-3.3-70b-versatile",
            "messages": [
                {"role": "system", "content": "あなたはトレンド分析と商品選定のプロです。JSON形式のみで回答してください。"},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.6,
            "response_format": {"type": "json_object"}
        })
        if res.status_code == 200:
            return json.loads(res.json()["choices"][0]["message"]["content"])
    except Exception as e:
        print(f"  ⚠️ LLMテーマ選定失敗: {e}")
    return {"theme": f"{category_name}のおすすめアイテム", "keywords": [category_name]}

# ─────────────────────────────────────────
# 楽天 API 商品取得
# ─────────────────────────────────────────

def extract_jan(item: dict):
    target_text = f"{item.get('itemCaption', '')} {item.get('itemName', '')} {item.get('itemCode', '')}"
    m = re.search(r'(4[59]\d{11})', target_text)
    if m: return m.group(1)
    for img_url in item.get('mediumImageUrls', []):
        m_img = re.search(r'(4[59]\d{11})', img_url)
        if m_img: return m_img.group(1)
    return ""

def clean_product_names_with_llm(products: list):
    if not products: return []
    product_names = [p["name"] for p in products]
    prompt = f"""以下の楽天の商品名リストから、余計なキャッチコピーをすべて排除し、
「ブランド名 + 商品名」のみの簡潔な名前に変換してください。
【リスト】
{chr(10).join(f"- {n}" for n in product_names)}
【出力形式（JSONのみ）】
{{"cleaned_names": ["ブランドA 商品X", ...]}}
"""
    try:
        res = requests.post("https://api.groq.com/openai/v1/chat/completions", headers={
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json"
        }, json={
            "model": "llama-3.3-70b-versatile",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.2,
            "response_format": {"type": "json_object"}
        })
        if res.status_code == 200:
            cleaned = json.loads(res.json()["choices"][0]["message"]["content"]).get("cleaned_names", [])
            for i, p in enumerate(products):
                if i < len(cleaned): p["name"] = cleaned[i]
            return products
    except: pass
    return products

def get_products_by_keywords(keywords, genre_id, count=6):
    """
    Geminiが提案したキーワードで楽天APIを検索し、高評価な商品を取得する。
    """
    product_pool = []
    seen_codes = set()
    
    headers = {"Referer": "https://www.mikke-style.com/", "Origin": "https://www.mikke-style.com/"}
    url = "https://openapi.rakuten.co.jp/ichibams/api/IchibaItem/Search/20220601"

    for kw in keywords:
        params = {
            "applicationId": RAKUTEN_APP_ID,
            "accessKey":     RAKUTEN_ACCESS_KEY,
            "keyword":        kw,
            "genreId":       genre_id,
            "minItemPrice":  1000,
            "maxItemPrice":  30000,
            "hits":           10,
            "sort":           "-reviewCount",
            "availability":   1,
            "formatVersion":  2,
        }
        try:
            time.sleep(1.0)
            res = requests.get(url, params=params, headers=headers, timeout=10)
            if res.status_code == 200:
                items = res.json().get("Items", [])
                for item in items:
                    code = item.get("itemCode")
                    if code not in seen_codes:
                        product_pool.append({
                            "name": item.get("itemName"),
                            "review_count": item.get("reviewCount", 0),
                            "jan": extract_jan(item)
                        })
                        seen_codes.add(code)
        except: pass
    
    if not product_pool: return []
    
    # レビュー数上位10件から6件選定
    product_pool.sort(key=lambda x: x["review_count"], reverse=True)
    top10 = product_pool[:10]
    selected = random.sample(top10, min(count, len(top10)))
    return clean_product_names_with_llm(selected)

def generate_article_title(theme, products):
    product_names = [p["name"] for p in products]
    prompt = f"テーマ: {theme}\n商品: {', '.join(product_names)}\n上記に基づき、思わずクリックしたくなるキャッチーな記事タイトルを1つ作成してください。"
    try:
        res = requests.post("https://api.groq.com/openai/v1/chat/completions", headers={
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json"
        }, json={
            "model": "llama-3.3-70b-versatile",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.7
        })
        if res.status_code == 200:
            return res.json()["choices"][0]["message"]["content"].strip().strip('"「」')
    except: pass
    return f"【発見】{theme}のおすすめ最新アイテム"

# ─────────────────────────────────────────
# Notion 登録・Discord 送信
# ─────────────────────────────────────────

def register_to_notion(title, category, products, publish_time):
    registered = 0
    for p in products:
        payload = {
            "parent": {"database_id": ARTICLE_MANAGE_DB_ID},
            "properties": {
                "商品名": {"title": [{"text": {"content": p["name"]}}]},
                "記事タイトル": {"rich_text": [{"text": {"content": title}}]},
                "カテゴリ": {"select": {"name": category}},
                "ステータス 1": {"select": {"name": "未処理"}},
                "公開時間": {"select": {"name": publish_time}},
                "JANコード": {"rich_text": [{"text": {"content": p["jan"]}}]}
            }
        }
        res = requests.post("https://api.notion.com/v1/pages", headers=NOTION_HEADERS, json=payload)
        if res.status_code == 200: registered += 1
    print(f"  ✅ Notion登録: {registered}/{len(products)} 件")

def send_to_discord(message):
    url = f"https://discord.com/api/v10/channels/{TARGET_CHANNEL_ID}/messages"
    payload = {"content": f"🍱 **おこげ編集長の本日のトレンド選定（{datetime.date.today()}）**\n\n{message}"}
    headers = {"Authorization": f"Bot {DISCORD_TOKEN}", "Content-Type": "application/json"}
    requests.post(url, headers=headers, json=payload)

# ─────────────────────────────────────────
# メイン
# ─────────────────────────────────────────

def main():
    print(f"--- Trend-based morning suggest started ---")
    
    # 1. トレンド取得
    print("📈 トレンド情報を収集中...")
    google_trends = fetch_google_trends()
    rakuten_hot = fetch_rakuten_hot_ranking()
    combined_trends = google_trends + rakuten_hot
    print(f"✅ トレンド取得完了: {len(combined_trends)}件")

    morning_cat, night_cat = get_daily_categories()
    plans = [{"time": "朝", "cat": morning_cat}, {"time": "夜", "cat": night_cat}]
    
    discord_msg = ""
    for plan in plans:
        t_label = plan["time"]
        cat = plan["cat"]
        print(f"\n✨ {t_label}の選定準備中 ({cat['name']})...")
        
        # 2-3. Gemini でテーマとキーワード決定
        gemini_decide = decide_theme_and_keywords(combined_trends, cat["name"])
        theme = gemini_decide["theme"]
        keywords = gemini_decide["keywords"]
        print(f"  💡 テーマ: {theme}")
        print(f"  🔍 キーワード: {keywords}")
        
        # 4-5. 楽天API検索と選定
        products = get_products_by_keywords(keywords, cat["genreId"])
        
        if products:
            title = generate_article_title(theme, products)
            print(f"  📌 タイトル: {title}")
            register_to_notion(title, cat["name"], products, t_label)
            
            discord_msg += f"**【{t_label}公開案】: {title}**\n"
            discord_msg += f"- カテゴリ: {cat['name']}\n"
            discord_msg += f"- テーマ: {theme}\n"
            discord_msg += f"- 選定キーワード: {', '.join(keywords)}\n\n"
        else:
            print("  ⚠️ 商品が見つかりませんでした。")

    if discord_msg:
        discord_msg += "📊 *Googleトレンド・楽天急上昇・Xの話題を分析し、消耗品を除外した「今、買うべき」アイテムを選定しました。*"
        send_to_discord(discord_msg)
        print("\n🎉 Success!")

if __name__ == "__main__":
    main()
