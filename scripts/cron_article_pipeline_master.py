#!/usr/bin/env python3
import os
import sys
import json
import re
import datetime
import urllib.parse
import subprocess
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv

# プロジェクトルートのパス
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(project_root, "scripts"))

# .env.local ロード
load_dotenv(os.path.join(project_root, ".env.local"))

NOTION_API_KEY = os.getenv("NOTION_API_KEY")
DATABASE_ID = "36cddb45-8772-80c3-ab74-eb061ecee73f"  # 「みっけ！競合記事キュー」のID

if not NOTION_API_KEY:
    print("❌ エラー: NOTION_API_KEY が .env.local に設定されていません。")
    sys.exit(1)

NOTION_HEADERS = {
    "Authorization": f"Bearer {NOTION_API_KEY}",
    "Notion-Version": "2022-06-28",
    "Content-Type": "application/json"
}

def generate_content_with_retry(model, prompt, max_retries=5, initial_delay=10):
    import time
    import google.api_core.exceptions
    
    # 予防的なウェイト（RPM制限回避のため、リクエスト間に必ず5秒のディレイを置く）
    time.sleep(5)
    
    delay = initial_delay
    for attempt in range(max_retries):
        try:
            return model.generate_content(prompt)
        except google.api_core.exceptions.ResourceExhausted as e:
            if attempt == max_retries - 1:
                raise e
            print(f"⚠️ Rate limit hit (429). Retrying in {delay} seconds... (Attempt {attempt+1}/{max_retries})")
            time.sleep(delay)
            delay *= 2
        except Exception as e:
            if "quota" in str(e).lower() or "429" in str(e):
                if attempt == max_retries - 1:
                    raise e
                print(f"⚠️ Quota/Rate limit hit (429). Retrying in {delay} seconds... (Attempt {attempt+1}/{max_retries})")
                time.sleep(delay)
                delay *= 2
            else:
                raise e

def get_existing_beauty_categories():
    categories = []
    articles_dir = os.path.join(project_root, "src", "content", "articles")
    if os.path.exists(articles_dir):
        for f in os.listdir(articles_dir):
            if f.endswith(".md"):
                path = os.path.join(articles_dir, f)
                try:
                    with open(path, "r", encoding="utf-8") as file:
                        content = file.read()
                        title_match = re.search(r'^title:\s*["\']?(.*?)["\']?\s*$', content, re.MULTILINE)
                        if title_match:
                            t = title_match.group(1)
                            cat = re.sub(r'おすすめ人気ランキング|のおすすめ|おすすめ|人気ランキング|の選び方|ランキング|比較|6選|8選|7選|選|【|】|！|。', '', t).strip()
                            if cat:
                                categories.append(cat)
                except Exception:
                    pass
                    
    # Notionの既存登録リストも取得
    try:
        url = f"https://api.notion.com/v1/databases/{DATABASE_ID}/query"
        res = requests.post(url, headers=NOTION_HEADERS, json={}, timeout=10)
        if res.status_code == 200:
            for page in res.json().get("results", []):
                name_prop = page["properties"].get("Name", {}).get("title") or []
                if name_prop:
                    name_str = name_prop[0].get("plain_text", "")
                    cat = re.sub(r'おすすめ人気ランキング|のおすすめ|おすすめ|人気ランキング|の選び方|ランキング|比較|6選|8選|7選|選', '', name_str).strip()
                    if cat:
                        categories.append(cat)
    except Exception as e:
        print(f"⚠️ Notion既存リストスキャンエラー: {e}")
        
    return list(set(categories))

def get_fallback_proposals(existing_categories):
    # あらかじめ用意された美容系カテゴリとクエリ
    candidates = [
        {"category": "アイクリーム", "search_query": "site:my-best.com アイクリーム おすすめ"},
        {"category": "まつげ美容液", "search_query": "site:my-best.com まつげ美容液 おすすめ"},
        {"category": "オールインワンジェル", "search_query": "site:my-best.com オールインワンジェル おすすめ"},
        {"category": "リップクリーム", "search_query": "site:my-best.com リップクリーム おすすめ"},
        {"category": "酵素洗顔料", "search_query": "site:my-best.com 酵素洗顔料 おすすめ"},
        {"category": "ピーリングジェル", "search_query": "site:my-best.com ピーリングジェル おすすめ"},
        {"category": "フェイススクラブ", "search_query": "site:my-best.com フェイススクラブ おすすめ"},
        {"category": "ネイルオイル", "search_query": "site:my-best.com ネイルオイル おすすめ"},
        {"category": "マッサージクリーム", "search_query": "site:my-best.com マッサージクリーム おすすめ"},
        {"category": "収れん化粧水", "search_query": "site:my-best.com 収れん化粧水 おすすめ"}
    ]
    proposals = []
    for c in candidates:
        is_duplicated = False
        for ext in existing_categories:
            if c["category"] in ext or ext in c["category"]:
                is_duplicated = True
                break
        if not is_duplicated:
            proposals.append(c)
    return proposals

def propose_new_beauty_categories(existing_categories):
    import google.generativeai as genai
    gemini_api_key = os.getenv("GEMINI_API_KEY")
    if not gemini_api_key:
        raise RuntimeError("GEMINI_API_KEY が .env.local に設定されていません。")
    genai.configure(api_key=gemini_api_key)

    prompt = f"""あなたは美容・スキンケアのトレンドに詳しい編集長です。
現在、以下のカテゴリについての美容・スキンケア系比較記事がすでに作成済み、または登録済みです。

【既存のカテゴリ・テーマ】
{json.dumps(existing_categories, ensure_ascii=False, indent=2)}

これらと**絶対に重複・類似しない**、新しい「美容・スキンケア」関連 of 小カテゴリ（顔用スキンケア、メイクアップ、ヘアケア、ボディケアなど）を6つ提案してください。
各カテゴリについて、my-best.comに実在する比較記事「[カテゴリ名]のおすすめ人気ランキング」を見つけるための、Google検索用クエリ（例: `site:my-best.com アイクリーム おすすめ`）を出力してください。

【出力フォーマット】
マークダウン装飾なしの純粋なJSON配列のみ。
[
  {{
    "category": "アイクリーム",
    "search_query": "site:my-best.com アイクリーム おすすめ"
  }},
  ...
]
"""
    try:
        model = genai.GenerativeModel("models/gemini-flash-lite-latest")
        response = generate_content_with_retry(model, prompt)
        response_text = response.text.strip()
        response_text = re.sub(r'^```json\s*|^```\s*|```$', '', response_text, flags=re.MULTILINE).strip()
        return json.loads(response_text)
    except Exception as e:
        print(f"⚠️ Geminiでのテーマ提案取得に失敗したため、フォールバックリストを使用します: {e}")
        return get_fallback_proposals(existing_categories)

def search_google_for_urls(query: str) -> list[str]:
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    }
    # GoogleはBotブロックが極めて厳しいため、Yahoo検索で代用する
    url = f"https://search.yahoo.co.jp/search?p={urllib.parse.quote(query)}"
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        if resp.status_code == 200:
            soup = BeautifulSoup(resp.text, 'html.parser')
            urls = []
            for a in soup.find_all('a', href=True):
                href = a['href']
                actual_url = ""
                if href.startswith('/url?q='):
                    actual_url = href.split('/url?q=')[1].split('&')[0]
                    actual_url = urllib.parse.unquote(actual_url)
                elif href.startswith('http://') or href.startswith('https://'):
                    actual_url = href
                
                if actual_url and ("https://my-best.com" in actual_url or "http://my-best.com" in actual_url):
                    parsed = urllib.parse.urlparse(actual_url)
                    if parsed.netloc == "my-best.com":
                        path = parsed.path
                        # 商品詳細(/products...)や検索ページ(/search...)を除外
                        if "/products" not in path and path != "/search" and path != "/search/":
                            clean_url = f"https://my-best.com{path}"
                            urls.append(clean_url)
            return list(dict.fromkeys(urls))
    except Exception as e:
        print(f"⚠️ Yahoo検索エラー: {e}")
    return []

def verify_and_get_page_title(url: str) -> str:
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    }
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        if resp.status_code == 200:
            soup = BeautifulSoup(resp.text, 'html.parser')
            title = soup.find('title')
            if title:
                title_text = title.string.strip()
                # my-bestのタイトルか確認
                if "おすすめ" in title_text or "ランキング" in title_text or "mybest" in title_text:
                    # mybest特有の「【2026年】...」や「 | mybest」をクリーンアップ
                    clean_title = re.sub(r'【.*?】|｜.*?| \|.*', '', title_text).strip()
                    return clean_title
    except Exception as e:
        print(f"⚠️ 実在確認エラー on {url}: {e}")
    return ""

def add_url_to_notion(name: str, url: str):
    payload = {
        "parent": { "database_id": DATABASE_ID },
        "properties": {
            "Name": {
                "title": [
                    { "text": { "content": name } }
                ]
            },
            "URL": {
                "url": url
            },
            "Category": {
                "select": {
                    "name": "美容・スキンケア"
                }
            },
            "Status": {
                "status": {
                    "name": "未処理"
                }
            }
        }
    }
    res = requests.post("https://api.notion.com/v1/pages", headers=NOTION_HEADERS, json=payload, timeout=10)
    return res.status_code == 200

def update_page_status(page_id: str, status_name: str):
    """Notionの特定ページのステータスプロパティを更新します。"""
    url = f"https://api.notion.com/v1/pages/{page_id}"
    payload = {
        "properties": {
            "Status": {
                "status": {"name": status_name}
            }
        }
    }
    try:
        requests.patch(url, headers=NOTION_HEADERS, json=payload, timeout=10)
    except Exception as e:
        print(f"⚠️ ステータス更新エラー: {e}")

def get_unprocessed_notion_pages(limit=3):
    url = f"https://api.notion.com/v1/databases/{DATABASE_ID}/query"
    payload = {
        "filter": {
            "property": "Status",
            "status": {
                "equals": "未処理"
            }
        },
        "sorts": [
            {
                "timestamp": "created_time",
                "direction": "ascending"
            }
        ],
        "page_size": limit
    }
    res = requests.post(url, headers=NOTION_HEADERS, json=payload, timeout=10)
    if res.status_code == 200:
        return res.json().get("results", [])
    else:
        print(f"❌ Notion「未処理」ページのクエリに失敗しました: {res.status_code} {res.text}")
        return []

def collect_existing_article_publish_dates():
    dates = set()
    articles_dir = os.path.join(project_root, "src", "content", "articles")
    if os.path.exists(articles_dir):
        for f in os.listdir(articles_dir):
            if f.endswith(".md"):
                path = os.path.join(articles_dir, f)
                try:
                    with open(path, "r", encoding="utf-8") as file:
                        content = file.read()
                        m = re.search(r'^publishDate:\s*["\']?(.*?)["\']?\s*$', content, re.MULTILINE)
                        if m:
                            date_str = m.group(1).strip()
                            dates.add(date_str)
                except Exception:
                    pass
    return dates

def calculate_next_article_publish_date(existing_dates_set, start_dt, allocated_dates):
    current_dt = start_dt
    while True:
        # 朝07:00
        dt_07 = current_dt.replace(hour=7, minute=0, second=0, microsecond=0)
        if dt_07 > start_dt:
            dt_str = dt_07.strftime("%Y-%m-%d %H:%M")
            if not any(dt_str in d for d in existing_dates_set) and not any(dt_str in d for d in allocated_dates):
                return dt_str
                
        # 夜19:00
        dt_19 = current_dt.replace(hour=19, minute=0, second=0, microsecond=0)
        if dt_19 > start_dt:
            dt_str = dt_19.strftime("%Y-%m-%d %H:%M")
            if not any(dt_str in d for d in existing_dates_set) and not any(dt_str in d for d in allocated_dates):
                return dt_str
                
        current_dt += datetime.timedelta(days=1)

def generate_article_draft(category_name, stockpile_data_str):
    import google.generativeai as genai
    
    rules_path = os.path.join(project_root, "GENERATION_RULES.md")
    prompt_path = os.path.join(project_root, "ARTICLE_PROMPT.md")
    config_path = os.path.join(project_root, "CATEGORY_CONFIG.yaml")
    faq_path = os.path.join(project_root, "FAQ_TEMPLATES.yaml")
    
    rules_content = ""
    if os.path.exists(rules_path):
        with open(rules_path, "r", encoding="utf-8") as f:
            rules_content = f.read()
            
    prompt_content = ""
    if os.path.exists(prompt_path):
        with open(prompt_path, "r", encoding="utf-8") as f:
            prompt_content = f.read()
            
    config_content = ""
    if os.path.exists(config_path):
        with open(config_path, "r", encoding="utf-8") as f:
            config_content = f.read()
            
    faq_content = ""
    if os.path.exists(faq_path):
        with open(faq_path, "r", encoding="utf-8") as f:
            faq_content = f.read()
            
    prompt = f"""あなたは、仕事も趣味も忙しい美容オタク女子ライターです。
親しみやすく崩したブログ口調で、読者に寄り添うように美容・スキンケア系の比較（ランキング）記事を執筆してください。

【記事執筆の絶対ルール】
以下のルールを100%厳密に遵守して執筆してください。特に「ですます調の完全廃止」「商品紹介文は必ず1000文字以上」「誇張表現や一人称の禁止」は絶対です。
{rules_content}

【構成とプロンプトの指示】
{prompt_content}

【カテゴリ設定とFAQテンプレート】
大カテゴリ: 美容・スキンケア
小カテゴリ: {category_name}
設定内容:
{config_content}

FAQテンプレート:
{faq_content}

【提供された商品事実データ (stockpile_data.json)】
このデータに基づいて各商品の特徴を執筆し、嘘の事実やスペックは創作しないでください。
提供された商品データ（最大6件）のすべてについて、順位順（第1位から第N位まで）に沿って漏れなくproducts配列に出力してください。途中で商品の執筆を打ち切ることは絶対に禁止します。
{stockpile_data_str}

【出力フォーマット】
マークダウンによるコードブロック装飾（```json や ```）は一切含めず、純粋なJSON文字列のみを返してください。
必ず以下のJSONスキーマ構造に100%適合させて出力してください。他の不要なキー（sections, title等）は絶対に含めないでください。

{{
  "meta": {{
    "title": "記事タイトル（意味の切れ目で読点や助詞の後に <br> を入れた自然な2行にする。例：まっさらな肌に、<br>うるおいの先手を。）",
    "excerpt": "80〜150文字のメタディスクリプション"
  }},
  "content": {{
    "intro": "200〜400文字の導入文（語尾はブログ調のカジュアルな口調。〜だよ、〜かも、など。一人称や誇張表現は禁止）",
    "summary": "200〜300文字のまとめ文（語尾はブログ調のカジュアルな口調。〜だよ、〜かも、など。一人称や誇張表現は禁止）"
  }},
  "products": [
    {{
      "name": "商品名（事実に基く正確な名称）",
      "description": "1000文字以上の詳細な商品説明（語尾はブログ調のカジュアルな口調。〜だよ、〜かも、など。一人称や誇張表現は禁止。factsにない機能の創作は禁止）",
      "analysis": {{
        "pros": ["メリット1（factsから直接言える内容、1文）", "メリット2"],
        "cons": ["デメリット1（factsから客観的に導ける内容。無ければ『特に気になるところは見当たらない優秀アイテムだよ』や『目立ったデメリットは特になし！』のように美容オタク女子ライターらしく表現する）"],
        "recommended_for": ["おすすめ対象1（recommended_forをそのまま使用）"]
      }}
    }}
  ],
  "ui": {{
    "points": ["選び方1", "選び方2", "選び方3"],
    "faq": [
      {{"question": "読者の疑問（商品名を含めない）", "answer": "回答（factsから確認できる情報のみ）"}}
    ]
  }}
}}
"""
    gemini_api_key = os.getenv("GEMINI_API_KEY")
    if gemini_api_key:
        genai.configure(api_key=gemini_api_key)
    model = genai.GenerativeModel("models/gemini-flash-lite-latest")
    response = generate_content_with_retry(model, prompt)
    response_text = response.text.strip()
    
    # JSON部分を抽出する頑健なロジック
    match = re.search(r'(\{.*\})', response_text, re.DOTALL)
    if match:
        response_text = match.group(1).strip()
    else:
        response_text = re.sub(r'^```json\s*|^```\s*|```$', '', response_text, flags=re.MULTILINE).strip()
    return response_text


def fix_article_draft_with_gemini(category_name, draft_json_str, error_message):
    import google.generativeai as genai
    
    prompt = f"""あなたは美容記事のバリデータエラーを修復するアシスタントです。
生成された比較記事のドラフト JSON に対し、以下のバリデーションエラーが発生しました。
エラー内容を完全に修正し、かつ以下の【正しいJSONスキーマ】に100%適合した正しいJSONデータを出力してください。

【カテゴリ】
{category_name}

【バリデーションエラー内容】
{error_message}

【正しいJSONスキーマ】
必ず以下の構造に完全に一致させて出力してください。他の不要なキー（sections, title等）は含めず、データをこのキー構造にマッピングし直してください。
{{
  "meta": {{
    "title": "記事タイトル（意味の切れ目で読点や助詞の後に <br> を入れた自然な2行にする。例：まっさらな肌に、<br>うるおいの先手を。）",
    "excerpt": "80〜150文字のメタディスクリプション"
  }},
  "content": {{
    "intro": "200〜400文字の導入文（語尾はブログ調のカジュアルな口調。〜だよ、〜かも、など。一人称や誇張表現は禁止）",
    "summary": "200〜300文字のまとめ文（語尾はブログ調のカジュアルな口調。〜だよ、〜かも、など。一人称や誇張表現は禁止）"
  }},
  "products": [
    {{
      "name": "商品名（事実に基く正確な名称）",
      "description": "1000文字以上の詳細な商品説明（語尾はブログ調のカジュアルな口調。〜だよ、〜かも、など。一人称や誇張表現は禁止。factsにない機能の創作は禁止）",
      "analysis": {{
        "pros": ["メリット1（factsから直接言える内容、1文）", "メリット2"],
        "cons": ["デメリット1（factsから客観的に導ける内容。無ければ『特に気になるところは見当たらない優秀アイテムだよ』や『目立ったデメリットは特になし！』のように美容オタク女子ライターらしく表現する）"],
        "recommended_for": ["おすすめ対象1（recommended_forをそのまま使用）"]
      }}
    }}
  ],
  "ui": {{
    "points": ["選び方1", "選び方2", "選び方3"],
    "faq": [
      {{"question": "読者の疑問（商品名を含めない）", "answer": "回答（factsから確認できる情報のみ）"}}
    ]
  }}
}}

【元のドラフト JSON】
{draft_json_str}

【修正の注意点】
- 商品紹介文 (description) の文字数が1000文字未満の場合は、各商品の特徴、使用感、他製品と比較したメリットをさらに詳細に描写して、必ず1000文字以上になるように文章を大幅に書き足してください。
- 「です・ます調（敬体）」は絶対に排除し、カジュアルなブログ口調（〜だよ、〜かも、など）に統一してください。
- 一人称（私、おこげなど）や誇張表現（マジで、ヤバい、神アイテム、最高、最強など）は絶対に削除してください。
- JSONとしての文法（ダブルクォーテーションの閉じ忘れ、改行のエスケープ漏れなど）を完璧に修正してください。

【出力フォーマット】
マークダウン装飾なしの純粋なJSON文字列。
"""
    gemini_api_key = os.getenv("GEMINI_API_KEY")
    if gemini_api_key:
        genai.configure(api_key=gemini_api_key)
    model = genai.GenerativeModel("models/gemini-flash-lite-latest")
    response = generate_content_with_retry(model, prompt)
    response_text = response.text.strip()
    
    # JSON部分を抽出する頑健なロジック
    match = re.search(r'(\{.*\})', response_text, re.DOTALL)
    if match:
        response_text = match.group(1).strip()
    else:
        response_text = re.sub(r'^```json\s*|^```\s*|```$', '', response_text, flags=re.MULTILINE).strip()
    return response_text


def save_and_validate_article_draft(draft_json_str):
    draft_path = os.path.join(project_root, "article_draft.json")
    try:
        data = json.loads(draft_json_str)
        with open(draft_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"⚠️ JSONパースエラー: {e}")
        return False, f"JSONパースエラー: {e}"
        
    res = subprocess.run(
        [sys.executable, os.path.join(project_root, "scripts", "validate_article_draft.py")],
        capture_output=True,
        text=True,
        encoding='utf-8'
    )
    if res.returncode == 0:
        return True, ""
    else:
        return False, res.stdout + res.stderr

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--all", action="store_true", help="Process all 6 unprocessed articles without quota split")
    args = parser.parse_args()

    # ロックファイルの取得（重複実行の防止）
    lock_file_path = os.path.join(project_root, "scripts", "cron_article_pipeline_master.lock")
    try:
        global lock_file
        lock_file = open(lock_file_path, "w")
        import fcntl
        fcntl.flock(lock_file, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except (IOError, BlockingIOError):
        print("❌ エラー: 別の自動生成プロセスが既に起動しています。重複実行を避けるため終了します。")
        sys.exit(0)

    print("🚀 比較記事自動生成パイプラインを開始します...")

    # ==========================================
    # STEP1: Notionに新しいmy-best URL 6件を自動登録
    # ==========================================
    print("\n[STEP 1] (Skipped) 未登録 of 美容・スキンケアカテゴリ提案と登録をスキップします。")
        # STEP1が失敗してもSTEP2には進む

    # ==========================================
    # STEP2: 6件を順番に処理
    # ==========================================
    # クォータ（1日20回制限）回避のため、デフォルトは1件ずつ処理。
    # --all フラグがある場合は制限なし（6件処理）。
    limit = 6 if args.all else 1
    print(f"\n[STEP 2] Notionから未処理の競合URLを取得して処理します（処理上限: {limit} 件）...")
    
    pages = get_unprocessed_notion_pages(limit=limit)
    if not pages:
        print("🎉 未処理のページはありません。処理を終了します。")
        sys.exit(0)
        
    print(f"取得した未処理ページ数: {len(pages)} 件")
    
    existing_dates = collect_existing_article_publish_dates()
    allocated_dates = []
    now = datetime.datetime.now()
    
    for idx, page in enumerate(pages, 1):
        page_id = page["id"]
        props = page["properties"]
        
        title_prop = props.get("Name", {}).get("title") or []
        name_str = title_prop[0].get("plain_text") if title_prop else "Untitled"
        
        competitor_url = props.get("URL", {}).get("url") or ""
        
        print(f"\n==================== [{idx}/{len(pages)}] {name_str} ====================")
        print(f"ページID: {page_id}")
        print(f"競合URL: {competitor_url}")
        
        res = subprocess.run(
            [sys.executable, "-u", os.path.join(project_root, "scripts", "prepare_stockpile_master.py"), page_id],
            env={**os.environ, "PYTHONIOENCODING": "utf-8"}
        )
        if res.returncode != 0:
            print(f"❌ prepare_stockpile.py が異常終了しました。このページをスキップします。")
            update_page_status(page_id, "未処理")
            continue
            
        print("✅ データ収集完了。")
        
        # stockpile_data.json の読み込みと小カテゴリ設定
        stockpile_path = os.path.join(project_root, "scripts", "stockpile_data.json")
        if not os.path.exists(stockpile_path):
            print(f"❌ stockpile_data.json が見つかりません。スキップします。")
            update_page_status(page_id, "未処理")
            continue
            
        with open(stockpile_path, "r", encoding="utf-8") as f:
            stockpile_data = json.load(f)
            
        # Notionタイトルから小カテゴリ名を抽出
        # 例：「アイクリームのおすすめ人気ランキング」 -> 「アイクリーム」
        category_name = re.sub(r'おすすめ人気ランキング|のおすすめ|おすすめ|人気ランキング|の選び方|ランキング|比較|6選|8選|7選|選', '', name_str).strip()
        print(f"小カテゴリ名: {category_name}")
        
        # stockpile_data.json の category フィールドを小カテゴリ名に書き換えて上書き
        stockpile_data["category"] = category_name
        with open(stockpile_path, "w", encoding="utf-8") as f:
            json.dump(stockpile_data, f, ensure_ascii=False, indent=2)
            
        # 2. article_draft.json を直接執筆
        print("⏳ article_draft.json を執筆中...")
        try:
            import copy
            temp_stockpile = copy.deepcopy(stockpile_data)
            temp_stockpile["products"] = temp_stockpile.get("products", [])[:6]
            draft_str = generate_article_draft(category_name, json.dumps(temp_stockpile, ensure_ascii=False))
        except Exception as e:
            print(f"❌ ドラフト生成失敗: {e}")
            update_page_status(page_id, "未処理")
            continue
            
        # 3. validate_article_draft.py でチェックと自己修復
        is_ok, err_msg = save_and_validate_article_draft(draft_str)
        retry_count = 0
        while not is_ok and retry_count < 5:
            retry_count += 1
            print(f"⚠️ バリデーション失敗。自己修復リトライ {retry_count}/5...")
            try:
                draft_str = fix_article_draft_with_gemini(category_name, draft_str, err_msg)
                is_ok, err_msg = save_and_validate_article_draft(draft_str)
            except Exception as e:
                print(f"⚠️ 自己修復処理中にエラーが発生しました: {e}")
                err_msg = str(e)
                
        if not is_ok:
            print(f"❌ 5回自己修復を試みましたがバリデーションを通過できませんでした。原因を報告してスキップします。")
            print(f"【最終エラーメッセージ】:\n{err_msg}")
            update_page_status(page_id, "未処理")
            continue
            
        print("✅ バリデーション成功！")
        
        # 4. publish_article.py で記事生成 & publishDate 設定
        publish_date = calculate_next_article_publish_date(existing_dates, now, allocated_dates)
        allocated_dates.append(publish_date)
        
        # slug を小カテゴリ名から自動決定
        # 例：「アイクリーム」 -> 「eye-cream」にするため、英名を取得（無ければカテゴリ名をローマ字化など）
        # 面倒を避けるため、Gemini に slug を決定させる（英小文字とハイフンのみ）
        import google.generativeai as genai
        gemini_api_key = os.getenv("GEMINI_API_KEY")
        if gemini_api_key:
            genai.configure(api_key=gemini_api_key)
        slug_prompt = f"「{category_name}」の英語スラッグ（英小文字とハイフンのみ、例: eye-cream, pore-cleanser など）を1語だけで出力してください。"
        model = genai.GenerativeModel("models/gemini-flash-lite-latest")
        slug = generate_content_with_retry(model, slug_prompt).text.strip().lower()
        slug = re.sub(r'[^a-z0-9\-]', '', slug)
        
        # 日付を含める
        date_prefix = publish_date.split(" ")[0].replace("-", "")
        full_slug = f"{date_prefix}-{slug}"
        print(f"割り当て公開日時: {publish_date}")
        print(f"スラグ: {full_slug}")
        
        print("⏳ 記事をパブリッシュ（publish_article.py 実行）中...")
        res = subprocess.run(
            [
                sys.executable, 
                "-u",
                os.path.join(project_root, "scripts", "publish_article.py"),
                "--title", category_name,
                "--category", "美容・スキンケア",
                "--slug", full_slug,
                "--date", publish_date
            ],
            env={**os.environ, "PYTHONIOENCODING": "utf-8"}
        )
        if res.returncode == 0:
            print(f"✅ パブリッシュ完了: {full_slug}.md")
            update_page_status(page_id, "完了")
            
            # クリーンアップ (古い一時JSONファイルを削除)
            subprocess.run(["rm", "-f", os.path.join(project_root, "scripts", "extracted_data_temp.json")])
            subprocess.run(["rm", "-f", os.path.join(project_root, "scripts", "prompt_temp.txt")])
            
            # git commit & push
            print("⏳ GitHubへのデプロイを実行中...")
            subprocess.run(["git", "add", "."])
            subprocess.run(["git", "commit", "-m", f"Publish {category_name} article via pipeline"])
            subprocess.run(["git", "push", "origin", "main"])
            print("✅ GitHubデプロイ完了。")
        else:
            print(f"❌ パブリッシュ失敗")
            update_page_status(page_id, "未処理")
            
    print("\n🎉 パイプラインの全処理が完了しました。")

if __name__ == "__main__":
    main()
