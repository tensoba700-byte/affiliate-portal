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

# ─────────────────────────────────────────
# AI新聞 Notion DBからたて・クロードのデータを取得
# ─────────────────────────────────────────

def get_all_shinbun_pages():
    """AI新聞ページ（子ページ一覧）をすべて取得する。"""
    url = f"https://api.notion.com/v1/blocks/{AI_SHINBUN_PARENT_ID}/children"
    res = requests.get(url, headers=NOTION_HEADERS)
    if res.status_code != 200:
        print(f"Error fetching AI新聞 pages: {res.text}")
        return []
    results = res.json().get("results", [])
    child_pages = [r for r in results if r["type"] == "child_page"]
    return child_pages


def parse_date_from_title(title: str) -> datetime.date | None:
    """
    ページタイトル「2026年4月20日」形式を datetime.date に変換する。
    解析失敗時は None を返す。
    """
    m = re.search(r'(\d{4})年(\d{1,2})月(\d{1,2})日', title)
    if m:
        try:
            return datetime.date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
        except ValueError:
            pass
    return None


def get_recent_shinbun_pages(days: int = 3) -> list[dict]:
    """
    AI新聞から直近 days 日分のページを取得する。
    タイトルが日付形式のページを対象にする。
    """
    all_pages = get_all_shinbun_pages()
    today = datetime.date.today()
    cutoff = today - datetime.timedelta(days=days)

    dated_pages = []
    for page in all_pages:
        title = page.get("child_page", {}).get("title", "")
        date = parse_date_from_title(title)
        if date and date >= cutoff:
            dated_pages.append({"id": page["id"], "title": title, "date": date})

    # 日付降順にソート（最新が先頭）
    dated_pages.sort(key=lambda x: x["date"], reverse=True)
    print(f"📅 AI新聞から直近{days}日分のページが {len(dated_pages)} 件見つかりました: "
          + ", ".join(p["title"] for p in dated_pages))
    return dated_pages


def get_page_content(page_id: str) -> dict:
    """
    指定ページのブロックを取得し、たて・クロード・おこげセクション別に分類して返す。
    """
    url = f"https://api.notion.com/v1/blocks/{page_id}/children"
    res = requests.get(url, headers=NOTION_HEADERS)
    if res.status_code != 200:
        return {"たて": [], "クロード": [], "おこげ": [], "その他": []}

    blocks = res.json().get("results", [])
    content_map = {"たて": [], "クロード": [], "おこげ": [], "その他": []}
    current_section = "その他"

    for b in blocks:
        if b["type"] == "heading_2":
            title = "".join([t["plain_text"] for t in b["heading_2"]["rich_text"]])
            if "たて" in title:
                current_section = "たて"
            elif "クロード" in title or "claude" in title.lower():
                current_section = "クロード"
            elif "おこげ" in title:
                current_section = "おこげ"
            else:
                current_section = "その他"
        elif b["type"] == "paragraph":
            text = "".join([t["plain_text"] for t in b["paragraph"]["rich_text"]])
            if text:
                content_map[current_section].append(text)
        elif b["type"] == "bulleted_list_item":
            text = "".join([t["plain_text"] for t in b["bulleted_list_item"]["rich_text"]])
            if text:
                content_map[current_section].append(f"* {text}")

    return content_map


def build_trend_context(days: int = 3) -> tuple[str, list[str]]:
    """
    直近 days 日分のAI新聞から「たて」「クロード」セクションの情報を集約し、
    プロンプト用テキストと過去タイトルリストを返す。
    """
    pages = get_recent_shinbun_pages(days)
    history_text = ""
    past_titles = []

    for page in pages:
        content = get_page_content(page["id"])
        date_label = page["title"]

        tate_lines = content.get("たて", [])
        claude_lines = content.get("クロード", [])
        okoge_lines = content.get("おこげ", [])

        # たて・クロードの情報をまとめる
        if tate_lines or claude_lines:
            history_text += f"\n=== {date_label} のトレンド情報 ===\n"
            if tate_lines:
                history_text += "【たて】\n" + "\n".join(tate_lines[:20]) + "\n"
            if claude_lines:
                history_text += "【クロード】\n" + "\n".join(claude_lines[:20]) + "\n"

        # おこげの過去提案タイトルを抽出（重複回避用）
        for line in okoge_lines:
            m = re.findall(r'[【「](2026年.*?)[】」]', line)
            past_titles.extend(m)
            m2 = re.findall(r'- (【2026年最新】.*)', line)
            past_titles.extend(m2)

    return history_text.strip(), list(set(past_titles))


# ─────────────────────────────────────────
# 企画提案 LLM
# ─────────────────────────────────────────

def generate_suggestions_with_llm(trend_context: str, past_titles: list[str]) -> dict | None:
    """
    たて・クロードのトレンド情報を元に、今日の記事企画3案をLLMに生成させる。
    """
    past_titles_text = "\n".join(f"- {t}" for t in past_titles) if past_titles else "なし"

    prompt = f"""あなたはトレンド分析のスペシャリスト兼コンテンツプランナーです。
以下の「AI新聞」から収集した直近3日分のトレンド情報（たて・クロード）を分析し、
今日書くべき最高のおすすめ記事ネタを3つ提案してください。

【直近3日間のトレンド情報（たて・クロード）】
{trend_context if trend_context else "※情報が取得できませんでした。一般的なトレンドから判断してください。"}

【過去の生成済み記事タイトル（重複厳禁！）】
{past_titles_text}

【企画選定の方針】
- たて・クロードが注目している最新トレンドを優先的に反映すること
- 季節性（現在は春）・イベント・話題性を考慮すること
- カテゴリ（美容・ガジェット・インテリア・生活雑貨・便利グッズ）が偏らないようにすること
- 過去タイトルと重複しないこと

【出力内容（JSON形式）】
必ず以下の構造のJSONのみを出力してください。
{{
  "suggestions": [
    {{
      "title": "記事タイトル案",
      "category": "美容/ガジェット/インテリア/生活雑貨/便利グッズから選択",
      "reason": "提案理由（たて・クロードのどの情報を参考にしたか含める）",
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


# ─────────────────────────────────────────
# 商品リスト生成・Notion登録・Discord送信
# ─────────────────────────────────────────

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


# ─────────────────────────────────────────
# メイン
# ─────────────────────────────────────────

def main():
    print(f"--- Morning suggest service started for {datetime.date.today()} ---")

    # AI新聞から直近3日分のたて・クロード情報を収集
    print("📰 AI新聞から直近3日分のたて・クロードのトレンド情報を取得中...")
    trend_context, past_titles = build_trend_context(days=3)

    if trend_context:
        print(f"✅ トレンド情報取得完了（{len(trend_context)}文字）")
    else:
        print("⚠️  トレンド情報が取得できませんでした。一般的なトレンドで提案します。")

    # LLMで企画を生成
    data = generate_suggestions_with_llm(trend_context, past_titles)
    if not data or "suggestions" not in data:
        print("Failed to generate suggestions.")
        return

    suggestions = data["suggestions"]
    print(f"Generated {len(suggestions)} suggestions.")

    # 最初の2件をNotionに登録
    registered_msg = ""
    for i in range(min(2, len(suggestions))):
        s = suggestions[i]
        print(f"Registering to Notion: {s['title']}")
        products = generate_products_for_topic(s['title'], s['category'])
        if products:
            register_to_notion(s['title'], s['category'], products)
            registered_msg += f"✅ **Notion登録完了**: {s['title']}（{len(products)}商品）\n"

    # Discord メッセージ作成
    discord_body = ""
    for i, s in enumerate(suggestions):
        marker = "📌 自動登録済み" if i < 2 else ""
        discord_body += f"\n**案{i+1}: {s['title']}** {marker}\n"
        discord_body += f"- カテゴリ: {s['category']}\n"
        discord_body += f"- 理由: {s['reason']}\n"
        discord_body += f"- ターゲット: {s['target']}\n"

    if registered_msg:
        discord_body += f"\n---\n{registered_msg}"

    # トレンド情報ソースを付記
    if trend_context:
        discord_body += "\n\n📰 *企画はNotionのAI新聞（直近3日分のたて・クロード情報）をもとに選定しました。*"

    success = send_to_discord(discord_body)
    if success:
        print("🎉 Successfully sent morning suggestions and registered topics!")
    else:
        print("❌ Failed to send to Discord.")

if __name__ == "__main__":
    main()
