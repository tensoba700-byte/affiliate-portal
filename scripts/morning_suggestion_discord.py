import os
import datetime
import json
import re
import sys
import requests
import xml.etree.ElementTree as ET
from dotenv import load_dotenv

# 標準出力を UTF-8 に設定（latin-1 エラー対策）
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

# Load credentials
load_dotenv("/Users/tsukika/Desktop/affiliate-portal/.env.local")
load_dotenv("/Users/tsukika/.gemini/antigravity/scratch/discord-bot/.env")

NOTION_API_KEY    = os.getenv("NOTION_API_KEY")
GROQ_API_KEY      = os.getenv("GROQ_API_KEY")
DISCORD_TOKEN     = os.getenv("DISCORD_TOKEN")
TARGET_CHANNEL_ID = os.getenv("TARGET_CHANNEL_ID")
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
            titles = [item.find('title').text for item in root.findall('.//item')][:20]
            return titles
    except Exception as e:
        print(f"⚠️ Google Trends 取得失敗: {e}")
    return []

# ─────────────────────────────────────────
# 企画生成 (LLM)
# ─────────────────────────────────────────

def generate_article_plans(trends):
    """
    トレンド情報を元に、朝と夜の2つの記事タイトルとカテゴリを決定する。
    """
    trend_text = "\n".join(f"- {t}" for t in trends) if trends else "現在、特定の急上昇ワードはありません。季節感のあるトピックを提案してください。"
    
    prompt = f"""現在のトレンド・季節情報:
{trend_text}
日付: {datetime.date.today()}

上記に基づき、アフィリエイトサイト「みっけ！」のための魅力的な記事企画を2つ提案してください。

【カテゴリ候補】
美容・スキンケア、ガジェット、インテリア、生活雑貨、便利グッズ

【出力条件】
- 朝用と夜用の2案を作成。
- カテゴリは上記候補から、トレンドに合うものを選ぶ。
- 読者が思わずクリックしたくなるようなキャッチーなタイトルにする。
- 日用消耗品そのものではなく、トレンドや季節の悩みを解決するテーマにする。

【出力形式（JSONのみ）】
{{
  "plans": [
    {{
      "title": "朝公開の記事タイトル案",
      "category": "選択したカテゴリ",
      "time": "朝"
    }},
    {{
      "title": "夜公開の記事タイトル案",
      "category": "選択したカテゴリ",
      "time": "夜"
    }}
  ]
}}
"""
    try:
        res = requests.post("https://api.groq.com/openai/v1/chat/completions", headers={
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json"
        }, json={
            "model": "llama-3.3-70b-versatile",
            "messages": [
                {"role": "system", "content": "あなたは凄腕のWebメディア編集長です。JSONのみを返してください。"},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.7,
            "response_format": {"type": "json_object"}
        })
        if res.status_code == 200:
            return json.loads(res.json()["choices"][0]["message"]["content"]).get("plans", [])
    except Exception as e:
        print(f"⚠️ 企画生成失敗: {e}")
    return []

# ─────────────────────────────────────────
# Notion 登録・Discord 送信
# ─────────────────────────────────────────

def register_to_notion(title, category, publish_time):
    """
    Notionに記事企画を登録する。商品は入れない。
    """
    payload = {
        "parent": {"database_id": ARTICLE_MANAGE_DB_ID},
        "properties": {
            "商品名":    {"title":     [{"text": {"content": ""}}]}, # 商品名は空
            "記事タイトル": {"rich_text": [{"text": {"content": title}}]},
            "カテゴリ":  {"select":    {"name": category}},
            "ステータス 1": {"select":  {"name": "未処理"}},
            "公開時間":  {"select":    {"name": publish_time}}
        }
    }
    res = requests.post("https://api.notion.com/v1/pages", headers=NOTION_HEADERS, json=payload)
    if res.status_code == 200:
        print(f"✅ Notion登録完了: {title} ({publish_time})")
    else:
        print(f"❌ Notion登録エラー: {res.text}")

def send_to_discord(plans):
    url = f"https://discord.com/api/v10/channels/{TARGET_CHANNEL_ID}/messages"
    body = "☀️ **おこげ編集長の本日の記事企画提案**\n\n"
    for p in plans:
        body += f"**【{p['time']}】{p['title']}**\n- カテゴリ: {p['category']}\n\n"
    
    body += "🚀 *Notionに「未処理」として登録しました。商品選定（たて担当）をお願いします。*"
    
    headers = {"Authorization": f"Bot {DISCORD_TOKEN}", "Content-Type": "application/json"}
    requests.post(url, headers=headers, json={"content": body})

# ─────────────────────────────────────────
# メイン
# ─────────────────────────────────────────

def main():
    print(f"--- Morning Planning Service Starting ---")
    
    # 1. トレンド取得
    print("📈 トレンド取得中...")
    trends = fetch_google_trends()
    
    # 2. 企画生成
    print("💡 記事企画を生成中...")
    plans = generate_article_plans(trends)
    
    if not plans:
        print("❌ 企画の生成に失敗しました。")
        return

    # 3. Notion登録
    for p in plans:
        register_to_notion(p["title"], p["category"], p["time"])
    
    # 4. Discord送信
    send_to_discord(plans)
    print("🎉 全ての処理が完了しました。")

if __name__ == "__main__":
    main()
