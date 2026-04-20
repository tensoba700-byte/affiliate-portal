import os
import datetime
import json
import random
import re
import time
import requests
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
# カテゴリ定義と回転ロジック
# ─────────────────────────────────────────

MIKKE_CATEGORIES = [
    {"name": "美容・スキンケア", "genreId": "100533"},
    {"name": "ガジェット", "genreId": "215783"},
    {"name": "インテリア", "genreId": "100804"},
    {"name": "生活雑貨", "genreId": "558885"},
    {"name": "便利グッズ", "genreId": "101211"}
]

def get_daily_categories():
    """
    今日の日付に基づいて、朝と夜で異なるカテゴリを選択する。
    """
    # 2024年1月1日からの経過日数でローテーション
    base_date = datetime.date(2024, 1, 1)
    days = (datetime.date.today() - base_date).days
    
    morning_idx = days % len(MIKKE_CATEGORIES)
    night_idx = (days + 1) % len(MIKKE_CATEGORIES)
    
    return MIKKE_CATEGORIES[morning_idx], MIKKE_CATEGORIES[night_idx]

# ─────────────────────────────────────────
# 楽天 API 商品取得
# ─────────────────────────────────────────

def extract_jan(item: dict):
    """アイテム情報からJANコードを抽出する。"""
    target_text = f"{item.get('itemCaption', '')} {item.get('itemName', '')} {item.get('itemCode', '')}"
    m = re.search(r'(4[59]\d{11})', target_text)
    if m:
        return m.group(1)
    for img_url in item.get('mediumImageUrls', []):
        m_img = re.search(r'(4[59]\d{11})', img_url)
        if m_img:
            return m_img.group(1)
    return ""

def clean_product_names_with_llm(products: list):
    """LLMを使って「ブランド名＋商品名」にクリーンアップする。"""
    if not products:
        return []
    product_names = [p["name"] for p in products]
    
    prompt = f"""以下の楽天の商品名リストから、余計なキャッチコピー（楽天1位、送料無料、ポイント、クーポン、★など）をすべて排除し、
「ブランド名 + 商品名」のみの簡潔な名前に変換してください。

【商品名リスト】
{chr(10).join(f"- {n}" for n in product_names)}

【出力形式（JSONのみ）】
{{
  "cleaned_names": ["ブランドA 商品X", "ブランドB 商品Y", ...]
}}
"""
    try:
        res = requests.post("https://api.groq.com/openai/v1/chat/completions", headers={
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json"
        }, json={
            "model": "llama-3.3-70b-versatile",
            "messages": [
                {"role": "system", "content": "あなたは商品データベースの編集者です。簡潔な「ブランド名 商品名」形式のJSONのみを返してください。"},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.2,
            "response_format": {"type": "json_object"}
        })
        if res.status_code == 200:
            cleaned = json.loads(res.json()["choices"][0]["message"]["content"]).get("cleaned_names", [])
            for i, p in enumerate(products):
                if i < len(cleaned):
                    p["name"] = cleaned[i]
            return products
    except Exception as e:
        print(f"  ⚠️ 名前クリーンアップ中にエラー: {e}")
    return products

def get_ranking_products(genre_id: str, count: int = 6):
    """
    指定カテゴリの楽天ランキング上位（レビュー数順）から、価格帯500円〜15000円の商品を取得。
    上位10件からランダムに count 件選ぶ。
    """
    params = {
        "applicationId": RAKUTEN_APP_ID,
        "accessKey":     RAKUTEN_ACCESS_KEY,
        "genreId":       genre_id,
        "minItemPrice":  500,
        "maxItemPrice":  15000,
        "hits":           30,
        "sort":           "-reviewCount",
        "availability":   1,
        "formatVersion":  2,
    }
    headers = {
        "Referer": "https://www.mikke-style.com/",
        "Origin": "https://www.mikke-style.com/"
    }
    url = "https://openapi.rakuten.co.jp/ichibams/api/IchibaItem/Search/20220601"
    
    try:
        time.sleep(1.5)
        res = requests.get(url, params=params, headers=headers, timeout=10)
        if res.status_code != 200:
            print(f"  楽天API エラー (Genre:{genre_id}): {res.status_code} {res.text[:100]}")
            return []

        items = res.json().get("Items", [])
        product_pool = []
        for item in items:
            name         = item.get("itemName", "").strip()
            review_count = item.get("reviewCount", 0)
            jan          = extract_jan(item)
            if name and len(name) > 5:
                product_pool.append({"name": name, "review_count": review_count, "jan": jan})

        # レビュー数上位10件からランダムに選定
        product_pool.sort(key=lambda x: x["review_count"], reverse=True)
        top10 = product_pool[:10]
        
        if not top10:
            return []
            
        selected = random.sample(top10, min(count, len(top10)))
        print(f"  ✨ 商品名をクリーンアップ中...")
        return clean_product_names_with_llm(selected)

    except Exception as e:
        print(f"  楽天API 例外: {e}")
        return []

# ─────────────────────────────────────────
# 企画タイトル生成 LLM
# ─────────────────────────────────────────

def generate_article_title(category_name, products):
    """
    選定された商品リストから、魅力的な記事タイトルをLLMに生成させる。
    """
    product_names = [p["name"] for p in products]
    prompt = f"""カテゴリ: {category_name}
選定商品:
{chr(10).join(f"- {n}" for n in product_names)}

これらの商品を掲載するアフィリエイト記事の、魅力的でクリックしたくなるタイトルを1つ考えてください。
読者の悩み（新生活、時短、コスパなど）に刺さる言葉を入れてください。

【出力形式】
タイトル文字列のみを出力してください。
"""
    try:
        res = requests.post("https://api.groq.com/openai/v1/chat/completions", headers={
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json"
        }, json={
            "model": "llama-3.3-70b-versatile",
            "messages": [
                {"role": "system", "content": "あなたはプロのWebライターです。最高にキャッチーな日本語のタイトルを1つだけ返してください。"},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.7
        })
        if res.status_code == 200:
            return res.json()["choices"][0]["message"]["content"].strip().strip('"「」')
    except:
        pass
    return f"【{datetime.date.today()}最新】{category_name}のおすすめアイテム選抜"

# ─────────────────────────────────────────
# Notion 登録・Discord 送信
# ─────────────────────────────────────────

def register_to_notion(title: str, category: str, products: list, publish_time: str):
    """Notionに商品を登録する。"""
    registered = 0
    for p in products:
        p_name = p.get("name", "Unknown Product")
        p_jan  = p.get("jan", "")
        payload = {
            "parent": {"database_id": ARTICLE_MANAGE_DB_ID},
            "properties": {
                "商品名":    {"title":     [{"text": {"content": p_name}}]},
                "記事タイトル": {"rich_text": [{"text": {"content": title}}]},
                "カテゴリ":  {"select":    {"name": category}},
                "ステータス 1": {"select":  {"name": "未処理"}},
                "公開時間":  {"select":    {"name": publish_time}},
                "JANコード": {"rich_text": [{"text": {"content": p_jan}}]}
            }
        }
        res = requests.post("https://api.notion.com/v1/pages", headers=NOTION_HEADERS, json=payload)
        if res.status_code == 200:
            registered += 1
    print(f"  ✅ Notion登録: {registered}/{len(products)} 件")

def send_to_discord(message: str):
    url     = f"https://discord.com/api/v10/channels/{TARGET_CHANNEL_ID}/messages"
    payload = {"content": f"☀️ **おこげ編集長からの本日の提案（{datetime.date.today()}）**\n\n{message}"}
    headers = {"Authorization": f"Bot {DISCORD_TOKEN}", "Content-Type": "application/json"}
    requests.post(url, headers=headers, json=payload)

# ─────────────────────────────────────────
# メイン
# ─────────────────────────────────────────

def main():
    print(f"--- Morning suggest service started for {datetime.date.today()} ---")
    
    morning_cat, night_cat = get_daily_categories()
    
    plans = [
        {"time": "朝", "cat": morning_cat},
        {"time": "夜", "cat": night_cat}
    ]
    
    discord_msg = ""
    
    for plan in plans:
        time_label = plan["time"]
        cat = plan["cat"]
        print(f"\n📝 {time_label}の企画準備中: {cat['name']}")
        
        # 楽天ランキングから商品取得
        products = get_ranking_products(cat["genreId"], count=6)
        
        if not products:
            print(f"  ⚠️ 商品が取得できませんでした。")
            continue
            
        # タイトル生成
        title = generate_article_title(cat["name"], products)
        print(f"  📌 タイトル: {title}")
        
        # Notion登録
        register_to_notion(title, cat["name"], products, time_label)
        
        # Discord用メッセージ
        discord_msg += f"**【{time_label}公開案】: {title}**\n"
        discord_msg += f"- カテゴリ: {cat['name']}\n"
        discord_msg += f"- 選定商品: {len(products)}点\n\n"

    if discord_msg:
        discord_msg += "🚀 *商品は楽天ランキング（500円〜15000円）からレビュー数上位をランダムに選定しました。*"
        send_to_discord(discord_msg)
        print("\n🎉 All tasks completed!")

if __name__ == "__main__":
    main()
