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

【出力内容（日本語）】
以下の項目をDiscord向けに分かりやすく3つ出力してください。
1. 記事タイトル案
2. 提案理由（トレンドや改善案の文脈から）
3. ターゲット層
"""

    res = requests.post("https://api.groq.com/openai/v1/chat/completions", headers={
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }, json={
        "model": "llama-3.3-70b-versatile",
        "messages": [
            {"role": "system", "content": "あなたは優秀な編集長として、簡潔かつ魅力的な提案を日本語で行ってください。"},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.5
    })
    
    if res.status_code == 200:
        return res.json()["choices"][0]["message"]["content"]
    else:
        return f"LLM Error: {res.text}"

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
        
    suggestion = generate_suggestions_with_llm(history)
    print("Generated suggestions. Sending to Discord...")
    
    success = send_to_discord(suggestion)
    if success:
        print("🎉 Successfully sent morning suggestions to Discord!")
    else:
        print("❌ Failed to send to Discord.")

if __name__ == "__main__":
    main()
