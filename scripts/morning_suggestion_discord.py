import os
import datetime
import json
import random
import re
import timequests
import re
import time
from dotenv import load_dotenv

# Load credentials
load_dotenv("/Users/tsukika/Desktop/affiliate-portal/.env.local")
load_dotenv("/Users/tsukika/.gemini/antigravity/scratch/discord-bot/.env")

NOTION_API_KEY    = os.getenv("NOTION_API_KEY")
GROQ_API_KEY      = os.getenv("GROQ_API_KEY")
DISCORD_TOKEN     = os.getenv("DISCORD_TOKEN")
TARGET_CHANNEL_ID = os.getenv("TARGET_CHANNEL_ID")
# 楽天 API
RAKUTEN_APP_ID    = os.getenv("RAKUTEN_APP_ID", "1f5612b1-7605-498d-923b-a18b22c64e1a")

AI_SHINBUN_PARENT_ID = "341ddb45-8772-80e2-8153-f4dec9e4e6b8"
ARTICLE_MANAGE_DB_ID = "8511908442c74738b78dc62f6a7a49d9"

NOTION_HEADERS = {
    "Authorization": f"Bearer {NOTION_API_KEY}",
    "Notion-Version": "2022-06-28",
    "Content-Type": "application/json"
}

# カテゴリ偏り管理（今回のバッチ実行内で使用済みカテゴリを追跡）
_used_categories: list[str] = []

# ─────────────────────────────────────────
# AI新聞 Notion DB からたて・クロードのデータを取得
# ─────────────────────────────────────────

def get_all_shinbun_pages() -> list[dict]:
    """AI新聞ページ（子ページ一覧）をすべて取得する。"""
    url = f"https://api.notion.com/v1/blocks/{AI_SHINBUN_PARENT_ID}/children"
    res = requests.get(url, headers=NOTION_HEADERS)
    if res.status_code != 200:
        print(f"Error fetching AI新聞 pages: {res.text}")
        return []
    results = res.json().get("results", [])
    return [r for r in results if r["type"] == "child_page"]


def parse_date_from_title(title: str):
    """ページタイトル「2026年4月20日」形式を datetime.date に変換する。"""
    m = re.search(r'(\d{4})年(\d{1,2})月(\d{1,2})日', title)
    if m:
        try:
            return datetime.date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
        except ValueError:
            pass
    return None


def get_recent_shinbun_pages(days: int = 3):
    """AI新聞から直近 days 日分のページを取得する。"""
    all_pages = get_all_shinbun_pages()
    today  = datetime.date.today()
    cutoff = today - datetime.timedelta(days=days)

    dated_pages = []
    for page in all_pages:
        title = page.get("child_page", {}).get("title", "")
        date  = parse_date_from_title(title)
        if date and date >= cutoff:
            dated_pages.append({"id": page["id"], "title": title, "date": date})

    dated_pages.sort(key=lambda x: x["date"], reverse=True)
    print(f"📅 AI新聞から直近{days}日分のページが {len(dated_pages)} 件見つかりました: "
          + ", ".join(p["title"] for p in dated_pages))
    return dated_pages


def get_page_content(page_id: str):
    """指定ページのブロックを取得し、たて・クロード・おこげセクション別に分類して返す。"""
    url = f"https://api.notion.com/v1/blocks/{page_id}/children"
    res = requests.get(url, headers=NOTION_HEADERS)
    if res.status_code != 200:
        return {"たて": [], "クロード": [], "おこげ": [], "その他": []}

    blocks = res.json().get("results", [])
    content_map   = {"たて": [], "クロード": [], "おこげ": [], "その他": []}
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


def build_trend_context(days: int = 3):
    """
    直近 days 日分のAI新聞から「たて」「クロード」セクションの情報を集約し、
    (プロンプト用テキスト, 過去タイトルリスト, トレンドキーワードリスト) を返す。
    """
    pages        = get_recent_shinbun_pages(days)
    history_text = ""
    past_titles  = []
    all_lines    = []   # キーワード抽出用

    for page in pages:
        content     = get_page_content(page["id"])
        date_label  = page["title"]
        tate_lines  = content.get("たて", [])
        claude_lines= content.get("クロード", [])
        okoge_lines = content.get("おこげ", [])

        if tate_lines or claude_lines:
            history_text += f"\n=== {date_label} のトレンド情報 ===\n"
            if tate_lines:
                history_text += "【たて】\n" + "\n".join(tate_lines[:20]) + "\n"
                all_lines.extend(tate_lines[:20])
            if claude_lines:
                history_text += "【クロード】\n" + "\n".join(claude_lines[:20]) + "\n"
                all_lines.extend(claude_lines[:20])

        for line in okoge_lines:
            m  = re.findall(r'[【「](2026年.*?)[】」]', line)
            past_titles.extend(m)
            m2 = re.findall(r'- (【2026年最新】.*)', line)
            past_titles.extend(m2)

    # 簡易キーワード抽出：2文字以上の名詞的フレーズを抜き出す
    keywords = extract_keywords(all_lines)

    return history_text.strip(), list(set(past_titles)), keywords


def extract_keywords(lines: list[str]) -> list[str]:
    """
    テキスト行のリストからトレンドキーワードを抽出する。
    括弧内・「」内・箇条書きの先頭フレーズを優先的に収集する。
    """
    keywords = set()
    for line in lines:
        # 「〇〇」形式
        for m in re.findall(r'「([^」]{2,20})」', line):
            keywords.add(m.strip())
        # 【〇〇】形式
        for m in re.findall(r'【([^】]{2,20})】', line):
            keywords.add(m.strip())
        # 箇条書き先頭（* や - の後）
        m = re.match(r'^[*\-・]\s*(.{2,25}?)(?:[。、\s]|$)', line)
        if m:
            keywords.add(m.group(1).strip())
        # カタカナ単語（製品名など）
        for m in re.findall(r'[ァ-ヶー]{3,}', line):
            keywords.add(m)

    # 汎用すぎる語は除外
    stop_words = {"今日", "昨日", "明日", "情報", "最新", "ニュース", "トレンド",
                  "おすすめ", "人気", "注目", "話題", "サービス", "システム"}
    return [k for k in keywords if k not in stop_words][:30]


# ─────────────────────────────────────────
# 楽天 API 商品検索
# ─────────────────────────────────────────

# 楽天ジャンルID マッピング（カテゴリ → 楽天 genreId）
RAKUTEN_GENRE_MAP = {
    "美容":       "100533",   # コスメ・香水・美容
    "美容・スキンケア": "100533",
    "ガジェット":  "215783",   # スマートフォン・タブレット
    "インテリア":  "100804",   # インテリア・寝具・収納
    "生活雑貨":   "558885",   # キッチン用品・食器
    "便利グッズ":  "100227",   # 日用品雑貨・文房具・手芸
    "家電":       "100227",
}


def search_rakuten_products(keyword: str, genre_id: str = "", count: int = 10):
    """
    楽天商品検索APIでキーワード検索し、レビュー数順で上位 count 件を返す。
    """
    # RAKUTEN_ACCESS_KEY を環境変数から取得
    RAKUTEN_ACCESS_KEY = os.getenv("RAKUTEN_ACCESS_KEY")

    params = {
        "applicationId": RAKUTEN_APP_ID,
        "accessKey":     RAKUTEN_ACCESS_KEY,  # accessKey を追加
        "keyword":        keyword,
        "hits":           30,
        "sort":           "-reviewCount",
        "availability":   1,
        "formatVersion":  2,
    }
    if genre_id:
        params["genreId"] = genre_id

    headers = {
        "Referer": "https://www.mikke-style.com/",
        "Origin": "https://www.mikke-style.com/"
    }

    try:
        # 新しいエンドポイントに変更
        url = "https://openapi.rakuten.co.jp/ichibams/api/IchibaItem/Search/20220601"
        time.sleep(1.5)
        res = requests.get(url, params=params, headers=headers, timeout=10)
        if res.status_code != 200:
            print(f"  楽天API エラー ({keyword}): {res.status_code} {res.text[:100]}")
            return []

        items = res.json().get("Items", [])
        results = []
        for item in items:
            name         = item.get("itemName", "").strip()
            review_count = item.get("reviewCount", 0)
            if name:
                results.append({"name": name, "review_count": review_count})

        results.sort(key=lambda x: x["review_count"], reverse=True)
        return results[:count]

    except Exception as e:
        print(f"  楽天API 例外 ({keyword}): {e}")
        return []


def fetch_products_via_rakuten(title: str, category: str, keywords: list[str]) -> list[str]:
    """
    記事タイトル・カテゴリ・トレンドキーワードを使って楽天APIを検索し、
    レビュー数上位10件から6商品をランダムに選んで商品名リストを返す。
    """
    genre_id = RAKUTEN_GENRE_MAP.get(category, "")

    # 検索キーワード候補を作成
    # 1. 記事タイトルから主要語を抽出
    title_keywords = re.findall(r'[ァ-ヶー]{3,}|[一-龥]{2,}', title)

    # 2. トレンドキーワードからカテゴリに関連しそうなものを優先
    category_hints = {
        "美容":      ["スキンケア", "美容液", "コスメ", "化粧水", "美白"],
        "美容・スキンケア": ["スキンケア", "美容液", "コスメ", "化粧水"],
        "ガジェット":  ["スマホ", "イヤホン", "充電器", "ワイヤレス", "Bluetooth"],
        "インテリア":  ["収納", "照明", "クッション", "ラグ", "棚"],
        "生活雑貨":   ["キッチン", "掃除", "洗濯", "収納", "日用品"],
        "便利グッズ":  ["便利", "アイデア", "コンパクト", "省スペース"],
    }
    hints = category_hints.get(category, [])

    # トレンドキーワードからカテゴリヒントに近いものを探す
    trend_kw = [k for k in keywords if any(h in k for h in hints)]
    if not trend_kw:
        trend_kw = keywords[:5]  # フォールバック：先頭5件

    # 検索クエリ候補（優先度順）
    search_queries = []
    if title_keywords:
        search_queries.append(" ".join(title_keywords[:3]))
    search_queries.extend(trend_kw[:3])
    if hints:
        search_queries.append(hints[0])
    # 最低1件は確保
    if not search_queries:
        search_queries = [category]

    print(f"  🔍 楽天API検索クエリ: {search_queries[:3]}")

    # 複数クエリで検索して商品プールを作成
    product_pool: list[dict] = []
    seen_names: set[str] = set()

    for query in search_queries[:3]:
        items = search_rakuten_products(query, genre_id=genre_id, count=10)
        for item in items:
            # 名前の重複・短すぎる商品名を除外
            clean_name = item["name"][:60].strip()  # 長すぎる名前をトリム
            if clean_name not in seen_names and len(clean_name) >= 5:
                product_pool.append({"name": clean_name, "review_count": item["review_count"]})
                seen_names.add(clean_name)

    if not product_pool:
        print(f"  ⚠️  楽天APIで商品が見つかりませんでした（{title}）")
        return []

    # レビュー数上位10件を抽出
    product_pool.sort(key=lambda x: x["review_count"], reverse=True)
    top10 = product_pool[:10]
    print(f"  📦 楽天API上位10件から選定（プール: {len(product_pool)}件）")

    # その中から6商品をランダム選択
    selected = random.sample(top10, min(6, len(top10)))
    return [p["name"] for p in selected]


# ─────────────────────────────────────────
# 企画提案 LLM
# ─────────────────────────────────────────

def generate_suggestions_with_llm(trend_context: str, past_titles: list):
    """たて・クロードのトレンド情報を元に、今日の記事企画3案をLLMに生成させる。"""
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
- 3案は必ず異なるカテゴリから選ぶこと
- 過去タイトルと重複しないこと

【出力内容（JSON形式）】
必ず以下の構造のJSONのみを出力してください。
{{
  "suggestions": [
    {{
      "title": "記事タイトル案",
      "category": "美容/ガジェット/インテリア/生活雑貨/便利グッズから選択",
      "reason": "提案理由（たて・クロードのどの情報を参考にしたか含める）",
      "target": "ターゲット層",
      "search_keyword": "楽天API検索用の日本語キーワード（商品を探すための具体的な語句）"
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
            {"role": "user",   "content": prompt}
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
# Notion 登録・Discord 送信
# ─────────────────────────────────────────

def register_to_notion(title: str, category: str, products: list[str], publish_time: str = "朝"):
    """
    Notionのアフィリエイト管理DBに商品を登録する。
    - 商品名: 楽天APIから取得した正確な商品名
    - 画像URL・アフィリエイトURLは登録しない（たてが担当）
    - publish_time: "朝" or "夜"
    """
    valid_categories = ["美容", "ガジェット", "インテリア", "生活雑貨", "便利グッズ", "美容・スキンケア", "家電"]
    final_category   = category
    for vc in valid_categories:
        if vc in category:
            final_category = vc
            break

    registered = 0
    for p in products:
        payload = {
            "parent": {"database_id": ARTICLE_MANAGE_DB_ID},
            "properties": {
                "商品名":    {"title":     [{"text": {"content": p}}]},
                "記事タイトル": {"rich_text": [{"text": {"content": title}}]},
                "カテゴリ":  {"select":    {"name": final_category}},
                "ステータス 1": {"select":  {"name": "未処理"}},
                "公開時間":  {"select":    {"name": publish_time}},
            }
        }
        res = requests.post("https://api.notion.com/v1/pages", headers=NOTION_HEADERS, json=payload)
        if res.status_code == 200:
            registered += 1
        else:
            print(f"  Error registering '{p}': {res.text[:200]}")

    print(f"  ✅ Notion登録: {registered}/{len(products)} 件")


def send_to_discord(message: str):
    url     = f"https://discord.com/api/v10/channels/{TARGET_CHANNEL_ID}/messages"
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

    # 1. AI新聞から直近3日分のたて・クロード情報を収集
    print("📰 AI新聞から直近3日分のたて・クロードのトレンド情報を取得中...")
    trend_context, past_titles, trend_keywords = build_trend_context(days=3)

    if trend_context:
        print(f"✅ トレンド情報取得完了（{len(trend_context)}文字 / キーワード{len(trend_keywords)}件）")
        print(f"   キーワード例: {trend_keywords[:8]}")
    else:
        print("⚠️  トレンド情報が取得できませんでした。一般的なトレンドで提案します。")

    # 2. LLMで企画を生成（search_keyword フィールドも取得）
    data = generate_suggestions_with_llm(trend_context, past_titles)
    if not data or "suggestions" not in data:
        print("Failed to generate suggestions.")
        return

    suggestions = data["suggestions"]
    print(f"💡 {len(suggestions)} 件の企画案を生成しました。")

    # 3. 最初の2件を楽天APIで商品検索してNotionに登録
    registered_msg  = ""
    publish_times   = ["朝", "夜"]

    for i in range(min(2, len(suggestions))):
        s       = suggestions[i]
        pt      = publish_times[i]
        title   = s["title"]
        cat     = s["category"]
        # LLMが提案した search_keyword を優先し、なければトレンドキーワードを使用
        llm_kw  = s.get("search_keyword", "")
        kw_list = ([llm_kw] + trend_keywords) if llm_kw else trend_keywords

        print(f"\n📝 案{i+1}: {title} ({cat}) / 公開時間: {pt}")
        print(f"   楽天API検索キーワード: {llm_kw or '(LLM未指定→トレンドKW使用)'}")

        # 楽天APIで実在商品を取得
        products = fetch_products_via_rakuten(title, cat, kw_list)

        if products:
            print(f"   選定商品 ({len(products)}件):")
            for p in products:
                print(f"     - {p}")
            register_to_notion(title, cat, products, publish_time=pt)
            registered_msg += (
                f"✅ **{title}**（{cat} / {pt}）\n"
                f"   └ 楽天API取得: {len(products)}商品\n"
            )
        else:
            print(f"   ⚠️  商品が取得できませんでした。スキップします。")
            registered_msg += f"⚠️ **{title}** — 商品取得失敗\n"

    # 4. Discord メッセージ作成
    discord_body = ""
    for i, s in enumerate(suggestions):
        marker = "📌 自動登録済み" if i < 2 else ""
        discord_body += f"\n**案{i+1}: {s['title']}** {marker}\n"
        discord_body += f"- カテゴリ: {s['category']}\n"
        discord_body += f"- 理由: {s['reason']}\n"
        discord_body += f"- ターゲット: {s['target']}\n"

    if registered_msg:
        discord_body += f"\n---\n{registered_msg}"

    if trend_context:
        discord_body += "\n\n📰 *企画はNotionのAI新聞（直近3日分のたて・クロード情報）＋楽天APIの人気商品をもとに選定しました。*"

    success = send_to_discord(discord_body)
    if success:
        print("\n🎉 Successfully sent morning suggestions and registered topics!")
    else:
        print("\n❌ Failed to send to Discord.")


if __name__ == "__main__":
    main()
