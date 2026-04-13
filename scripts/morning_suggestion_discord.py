import os
import datetime
import json
import requests
import re
from dotenv import load_dotenv

# Load credentials
load_dotenv("/Users/tsukika/Desktop/affiliate-portal/.env.local")
load_dotenv("/Users/tsukika/.gemini/antigravity/scratch/discord-bot/.env")

NOTION_API_KEY = os.getenv("NOTION_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
TARGET_CHANNEL_ID = os.getenv("TARGET_CHANNEL_ID")
AI_SHINBUN_PARENT_ID = "341ddb45-8772-80e2-8153-f4dec9e4e6b8"
ARTICLE_MANAGE_DB_ID = "8511908442c74738b78dc62f6a7a49d9"

NOTION_HEADERS = {
    "Authorization": f"Bearer {NOTION_API_KEY}",
    "Notion-Version": "2022-06-28",
    "Content-Type": "application/json"
}

def get_recent_pages(limit=7):
    url = f"https://api.notion.com/v1/blocks/{AI_SHINBUN_PARENT_ID}/children"
    res = requests.get(url, headers=NOTION_HEADERS)
    if res.status_code != 200:
        print(f"Error fetching Notion pages: {res.text}")
        return []
        
    results = res.json().get("results", [])
    child_pages = [r for r in results if r["type"] == "child_page"]
    # Sort and take the most recent ones (Notion results are usually chronologically ordered)
    return child_pages[-limit:]

def get_page_content(page_id):
    url = f"https://api.notion.com/v1/blocks/{page_id}/children"
    res = requests.get(url, headers=NOTION_HEADERS)
    if res.status_code != 200: return ""
    
    blocks = res.json().get("results", [])
    content_map = {"たて": [], "クロード": [], "おこげ": [], "その他": []}
    current_section = "その他"
    
    for b in blocks:
        if b["type"] == "heading_2":
            title = "".join([t["plain_text"] for t in b["heading_2"]["rich_text"]])
            if "たて" in title: current_section = "たて"
            elif "クロード" in title: current_section = "クロード"
            elif "おこげ" in title: current_section = "おこげ"
            else: current_section = "その他"
        elif b["type"] == "paragraph":
            text = "".join([t["plain_text"] for t in b["paragraph"]["rich_text"]])
            if text: content_map[current_section].append(text)
        elif b["type"] == "bulleted_list_item":
            text = "".join([t["plain_text"] for t in b["bulleted_list_item"]["rich_text"]])
            if text: content_map[current_section].append(f"* {text}")
            
    return content_map

def generate_suggestions_with_llm(history):
    history_text = ""
    past_titles = []
    
    for i, day in enumerate(history):
        history_text += f"\n--- Day {i+1} ---\n"
        history_text += "## Trends (Claude & Tate):\n" + "\n".join(day["たて"] + day["クロード"])
        history_text += "\n## My Suggestions/Improvements (Okoge):\n" + "\n".join(day["おこげ"])
        
        # Extract past titles to avoid duplicates
        for line in day["おこげ"]:
            if "今日生成した記事タイトル" in line: continue
            m = re.findall(r'- (【2026年最新】.*)', line)
            if m: past_titles.extend(m)

    prompt = f"""あなたはトレンド分析のスペシャリスト兼コンテンツプランナーです。
以下の直近1週間の「AI新聞」の内容（トレンド情報、過去の提案、生成済み記事）を分析し、
今日書くべき最高のおすすめ記事ネタを3つ提案してください。

【過去の生成済み記事タイトル（重複厳禁！）】
{chr(10).join(set(past_titles))}

【直近1週間のトレンド・改善案ログ】
{history_text}

【出力内容（JSON形式）】
必ず以下の構造のJSONのみを出力してください。
{{
  "suggestions": [
    {{
      "title": "記事タイトル案",
      "category": "美容/ガジェット/インテリア/生活雑貨/便利グッズから選択",
      "reason": "提案理由",
      "target": "ターゲット層"
    }},
    ... (合計3つ)
  ]
}}
"""

    res = requests.post("https://api.groq.com/openai/v1/chat/completions", headers={
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }, json={
        "model": "llama-3.3-70b-versatile",
        "messages": [
            {"role": "system", "content": "あなたは優秀な編集長として、簡潔かつ魅力的な提案を日本語で行ってください。JSON以外のテキストは一切含めないでください。"},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.4,
        "response_format": {"type": "json_object"}
    })
    
    if res.status_code == 200:
        return json.loads(res.json()["choices"][0]["message"]["content"])
    else:
        print(f"LLM Error: {res.text}")
        return None

def generate_products_for_topic(title, category):
    prompt = f"""記事タイトル: 「{title}」
カテゴリ: {category}

この記事に掲載する、アフィリエイトで成約率の高そうな具体的かつ最新の人気商品を「5個から7個」リストアップしてください。

【出力形式（JSONのみ）】
{{
  "products": ["商品名1", "商品名2", ...]
}}
"""
    res = requests.post("https://api.groq.com/openai/v1/chat/completions", headers={
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }, json={
        "model": "llama-3.3-70b-versatile",
        "messages": [
            {"role": "system", "content": "指定されたJSON形式のみで回答してください。"},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.5,
        "response_format": {"type": "json_object"}
    })
    
    if res.status_code == 200:
        return json.loads(res.json()["choices"][0]["message"]["content"]).get("products", [])
    else:
        return []

def register_to_notion(title, category, products):
    # Mapping to known valid categories in Notion
    valid_categories = ["美容", "ガジェット", "インテリア", "生活雑貨", "便利グッズ", "美容・スキンケア", "家電"]
    final_category = category
    for vc in valid_categories:
        if vc in category:
            final_category = vc
            break

    for p in products:
        payload = {
            "parent": { "database_id": ARTICLE_MANAGE_DB_ID },
            "properties": {
                "商品名": { "title": [{ "text": { "content": p } }] },
                "記事タイトル": { "rich_text": [{ "text": { "content": title } }] },
                "カテゴリ": { "select": { "name": final_category } },
                "ステータス 1": { "select": { "name": "未処理" } }
            }
        }
        res = requests.post("https://api.notion.com/v1/pages", headers=NOTION_HEADERS, json=payload)
        if res.status_code != 200:
            print(f"Error registering product {p}: {res.text}")

def send_to_discord(message):
    url = f"https://discord.com/api/v10/channels/{TARGET_CHANNEL_ID}/messages"
    payload = {
        "content": f"☀️ **おこげ編集長からの朝の提案（{datetime.date.today()}）**\n\n{message}"
    }
    headers = {
        "Authorization": f"Bot {DISCORD_TOKEN}",
        "Content-Type": "application/json"
    }
    res = requests.post(url, headers=headers, json=payload)
    return res.status_code == 200

def main():
    print(f"--- Morning suggest service started for {datetime.date.today()} ---")
    pages = get_recent_pages(7)
    if not pages:
        print("No historical data found in Notion.")
        return
        
    history = []
    for p in pages:
        history.append(get_page_content(p["id"]))
        
    data = generate_suggestions_with_llm(history)
    if not data or "suggestions" not in data:
        print("Failed to generate suggestions.")
        return
        
    suggestions = data["suggestions"]
    print(f"Generated {len(suggestions)} suggestions.")

    # Register the first 2 suggestions to Notion
    registered_msg = ""
    for i in range(min(2, len(suggestions))):
        s = suggestions[i]
        print(f"Registering to Notion: {s['title']}")
        products = generate_products_for_topic(s['title'], s['category'])
        if products:
            register_to_notion(s['title'], s['category'], products)
            registered_msg += f"✅ **Notion登録完了**: {s['title']}（{len(products)}商品）\n"

    # Prepare Discord message
    discord_body = ""
    for i, s in enumerate(suggestions):
        marker = "📌 自動登録済み" if i < 2 else ""
        discord_body += f"\n**案{i+1}: {s['title']}** {marker}\n"
        discord_body += f"- カテゴリ: {s['category']}\n"
        discord_body += f"- 理由: {s['reason']}\n"
        discord_body += f"- ターゲット: {s['target']}\n"
        
    if registered_msg:
        discord_body += f"\n---\n{registered_msg}"

    success = send_to_discord(discord_body)
    if success:
        print("🎉 Successfully sent morning suggestions and registered topics!")
    else:
        print("❌ Failed to send to Discord.")

if __name__ == "__main__":
    main()
