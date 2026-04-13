import os
import datetime
import json
import requests
import glob
import re
from dotenv import load_dotenv

# Load credentials
load_dotenv("/Users/tsukika/Desktop/affiliate-portal/.env.local")
load_dotenv("/Users/tsukika/.gemini/antigravity/scratch/discord-bot/.env")
NOTION_API_KEY = os.getenv("NOTION_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
AI_SHINBUN_PARENT_ID = "341ddb45-8772-80e2-8153-f4dec9e4e6b8"

NOTION_HEADERS = {
    "Authorization": f"Bearer {NOTION_API_KEY}",
    "Notion-Version": "2022-06-28",
    "Content-Type": "application/json"
}

def get_today_articles():
    articles_dir = "/Users/tsukika/Desktop/affiliate-portal/src/content/articles/*.md"
    today_files = []
    
    for file_path in glob.glob(articles_dir):
        mtime = datetime.datetime.fromtimestamp(os.path.getmtime(file_path))
        if mtime.date() == datetime.date.today():
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
                # Extract title from frontmatter
                m = re.search(r'title: "(.*?)"', content)
                title = m.group(1) if m else os.path.basename(file_path)
                today_files.append({"path": file_path, "title": title, "content": content})
                
    return today_files

def get_weekly_stats():
    today = datetime.date.today()
    last_week = today - datetime.timedelta(days=7)
    articles_dir = "/Users/tsukika/Desktop/affiliate-portal/src/content/articles/*.md"
    
    counts = {
        "美容": 0,
        "ガジェット": 0,
        "インテリア": 0,
        "生活雑貨": 0,
        "便利グッズ": 0
    }
    others = {}

    for file_path in glob.glob(articles_dir):
        mtime = datetime.date.fromtimestamp(os.path.getmtime(file_path))
        if mtime >= last_week:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                    m = re.search(r'category: "(.*?)"', content)
                    if m:
                        cat = m.group(1)
                        # Normalize category name
                        found = False
                        for key in counts.keys():
                            if key in cat:
                                counts[key] += 1
                                found = True
                                break
                        if not found:
                            others[cat] = others.get(cat, 0) + 1
            except Exception as e:
                print(f"Error reading {file_path}: {e}")

    stats_text = ""
    for cat, count in counts.items():
        stats_text += f"　- {cat}：{count}本\n"
    for cat, count in others.items():
        stats_text += f"　- {cat}：{count}本\n"
    
    return stats_text.strip()

def analyze_with_llm(articles):
    if not articles:
        return {
            "titles": "本日の生成記事はありません。",
            "suggestions": "・新製品発表予定のガジェットレビュー\n・季節の変わり目のスキンケア商品\n・在宅ワークを快適にするインテリア",
            "best_phrase": "なし",
            "ai_like": "なし",
            "improvement": "N/A"
        }

    article_titles = "\n".join([f"- {a['title']}" for a in articles])
    combined_content = "\n\n---\n\n".join([a['content'][:2000] for a in articles]) # Limit content size

    prompt = f"""あなたは「みっけ！」アフィリエイトポータルの編集長「おこげ」です。
今日生成された以下の記事をレビューし、レポートをJSON形式で作成してください。

【今日生成された記事】
{article_titles}

【記事の内容（一部）】
{combined_content}

【出力形式（厳守）】
{{
  "suggestions": "明日のおすすめネタ3つとその理由（箇条書き）",
  "best_phrase": "今日の記事で最も心に響いたフレーズ",
  "ai_like": "AIっぽくなってしまった機械的な表現",
  "improvement": "改善案"
}}
"""

    res = requests.post("https://api.groq.com/openai/v1/chat/completions", headers={
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }, json={
        "model": "llama-3.3-70b-versatile",
        "messages": [
            {"role": "system", "content": "あなたは編集長「おこげ」です。必ず指定された英語キーのJSONのみを出力してください。"},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.4,
        "response_format": {"type": "json_object"}
    })

    if res.status_code == 200:
        raw_content = res.json()["choices"][0]["message"]["content"]
        print(f"DEBUG: Raw LLM Output: {raw_content}")
        data = json.loads(raw_content)
        
        # Mapping possible Japanese keys back to English if they occur
        mapping = {
            "おすすめネタ": "suggestions",
            "心に響いたフレーズ": "best_phrase",
            "AIっぽい表現": "ai_like",
            "改善案": "improvement"
        }
        for jp, en in mapping.items():
            if jp in data and en not in data:
                data[en] = data[jp]
        
        # Ensure all keys exist
        for key in ["suggestions", "best_phrase", "ai_like", "improvement"]:
            if key not in data:
                data[key] = "情報なし"
                
        data["titles"] = article_titles
        return data
    else:
        print(f"LLM Error: {res.text}")
        return None

def find_or_create_daily_page():
    now = datetime.datetime.now()
    page_title = f"{now.year}年{now.month}月{now.day}日"
    
    # 1. Search for existing page
    url = f"https://api.notion.com/v1/blocks/{AI_SHINBUN_PARENT_ID}/children"
    res = requests.get(url, headers=NOTION_HEADERS)
    children = res.json().get("results", [])
    
    for child in children:
        if child["type"] == "child_page" and child["child_page"]["title"] == page_title:
            return child["id"]

    # 2. Create new page if not found
    create_url = "https://api.notion.com/v1/pages"
    payload = {
        "parent": {"page_id": AI_SHINBUN_PARENT_ID},
        "properties": {
            "title": {"title": [{"text": {"content": page_title}}]}
        }
    }
    res = requests.post(create_url, headers=NOTION_HEADERS, json=payload)
    if res.status_code == 200:
        return res.json()["id"]
    else:
        print(f"Error creating page: {res.text}")
        return None

def append_report_to_page(page_id, report):
    url = f"https://api.notion.com/v1/blocks/{page_id}/children"
    
    # Ensure suggestions is a string
    suggestions = report["suggestions"]
    if isinstance(suggestions, list):
        suggestions = "\n".join([f"・{s}" for s in suggestions])
    
    blocks = [
        {
            "object": "block",
            "type": "heading_2",
            "heading_2": {
                "rich_text": [{"type": "text", "text": {"content": "おこげ"}}]
            }
        },
        {
            "object": "block",
            "type": "paragraph",
            "paragraph": {
                "rich_text": [{"type": "text", "text": {"content": "■ 今日生成した記事タイトル", "link": None}, "annotations": {"bold": True}}]
            }
        },
        {
            "object": "block",
            "type": "paragraph",
            "paragraph": {
                "rich_text": [{"type": "text", "text": {"content": report["titles"]}}]
            }
        },
        {
            "object": "block",
            "type": "paragraph",
            "paragraph": {
                "rich_text": [{"type": "text", "text": {"content": "■ 明日のおすすめ記事ネタ3つ（理由付き）", "link": None}, "annotations": {"bold": True}}]
            }
        },
        {
            "object": "block",
            "type": "paragraph",
            "paragraph": {
                "rich_text": [{"type": "text", "text": {"content": suggestions}}]
            }
        },
        {
            "object": "block",
            "type": "paragraph",
            "paragraph": {
                "rich_text": [{"type": "text", "text": {"content": "■ 今日の記事で良かったフレーズ", "link": None}, "annotations": {"bold": True}}]
            }
        },
        {
            "object": "block",
            "type": "paragraph",
            "paragraph": {
                "rich_text": [{"type": "text", "text": {"content": report["best_phrase"]}}]
            }
        },
        {
            "object": "block",
            "type": "paragraph",
            "paragraph": {
                "rich_text": [{"type": "text", "text": {"content": "■ AIっぽくなってしまった表現と改善案", "link": None}, "annotations": {"bold": True}}]
            }
        },
        {
            "object": "block",
            "type": "paragraph",
            "paragraph": {
                "rich_text": [
                    {"type": "text", "text": {"content": "【原文】: "}, "annotations": {"bold": True}},
                    {"type": "text", "text": {"content": report["ai_like"] + "\n"}},
                    {"type": "text", "text": {"content": "【改善案】: "}, "annotations": {"bold": True, "color": "green"}},
                    {"type": "text", "text": {"content": report["improvement"]}}
                ]
            }
        },
        {
            "object": "block",
            "type": "paragraph",
            "paragraph": {
                "rich_text": [{"type": "text", "text": {"content": "■ 今週のカテゴリ別投稿数（偏りチェック）", "link": None}, "annotations": {"bold": True}}]
            }
        },
        {
            "object": "block",
            "type": "paragraph",
            "paragraph": {
                "rich_text": [{"type": "text", "text": {"content": report["weekly_stats"]}}]
            }
        }
    ]
    
    res = requests.patch(url, headers=NOTION_HEADERS, json={"children": blocks})
    return res.status_code == 200

def main():
    print(f"--- Starting Daily Report for {datetime.date.today()} ---")
    articles = get_today_articles()
    print(f"Found {len(articles)} articles generated today.")
    
    report = analyze_with_llm(articles)
    if not report:
        print("Analysis failed.")
        return

    # Add weekly stats to report
    report["weekly_stats"] = get_weekly_stats()

    page_id = find_or_create_daily_page()
    if not page_id:
        print("Could not find/create Notion page.")
        return

    success = append_report_to_page(page_id, report)
    if success:
        print("🎉 Successfully posted report to Notion!")
    else:
        print("❌ Failed to post report.")

if __name__ == "__main__":
    main()
