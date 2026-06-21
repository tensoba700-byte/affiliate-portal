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

# プロジェクトルート
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(project_root, "scripts"))

# .env.local ロード
load_dotenv(os.path.join(project_root, ".env.local"))

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

def get_existing_columns():
    columns_dir = os.path.join(project_root, "src", "content", "columns")
    existing = []
    if os.path.exists(columns_dir):
        for f in os.listdir(columns_dir):
            if f.endswith(".md"):
                path = os.path.join(columns_dir, f)
                try:
                    with open(path, "r", encoding="utf-8") as file:
                        content = file.read()
                        title_match = re.search(r'^title:\s*["\']?(.*?)["\']?\s*$', content, re.MULTILINE)
                        title = title_match.group(1).strip() if title_match else f[:-3]
                        existing.append({"slug": f[:-3], "title": title})
                except Exception as e:
                    print(f"Error reading existing column {f}: {e}")
    return existing

def get_existing_articles():
    articles_dir = os.path.join(project_root, "src", "content", "articles")
    existing = []
    if os.path.exists(articles_dir):
        for f in os.listdir(articles_dir):
            if f.endswith(".md"):
                path = os.path.join(articles_dir, f)
                try:
                    with open(path, "r", encoding="utf-8") as file:
                        content = file.read()
                        title_match = re.search(r'^title:\s*["\']?(.*?)["\']?\s*$', content, re.MULTILINE)
                        title = title_match.group(1).strip() if title_match else f[:-3]
                        existing.append({"slug": f[:-3], "title": title})
                except Exception as e:
                    print(f"Error reading existing article {f}: {e}")
    return existing

def select_themes(existing_columns, existing_articles, current_month):
    import google.generativeai as genai
    gemini_api_key = os.getenv("GEMINI_API_KEY")
    if not gemini_api_key:
        raise RuntimeError("GEMINI_API_KEY が .env.local に設定されていません。")
    genai.configure(api_key=gemini_api_key)
    
    prompt = f"""あなたは美容コラム記事の優秀な編集長です。
現在運用中の美容情報サイト「みっけ！」において、AdSense収益とSEO流入を最大化するため、新着コラム記事のテーマを14本分選定してください。

コラム記事は商品を紹介しない、純粋な美容知識・情報提供のための記事です。
以下のルールを厳密に守ってテーマを選定してください。

【テーマ選定のルール】
1. テーマの3系統（①FAQ深掘り型、②生活・知識型、③季節・トレンド型）からバランスよく14本分選定すること。
2. 既存 of コラム記事のテーマやスラグと絶対に重複・類似しないこと。切り口を変える場合は、より具体的でターゲットを絞ったものにすること。
3. FAQ深掘り型の場合は、既存の比較記事（ランキング記事）に関連するテーマを選び、内部リンクを繋げられるようにすること。
4. 季節・トレンド型では、現在の月（{current_month}月）に合わせた季節要因（例: 梅雨のテカリ、紫外線対策、インナードライ、毛穴など）を取り入れること。
5. 各テーマに対し、画像生成用のシンプルな被写体（英語名詞1語、例: sunscreen, flower, green leaves, cosmetic bottle, dropper など）を決定すること。被写体には人物、テキスト、ロゴを含めてはなりません。
6. コラムのタイトルは、ルールに基づき「[情緒的なメインタイトル（20文字以内）]【[検索キーワードを含むサブタイトル（30文字以内）]】」の形式にすること。

【既存のコラム記事リスト】
{json.dumps(existing_columns, ensure_ascii=False, indent=2)}

【既存の比較（ランキング）記事リスト】
{json.dumps(existing_articles, ensure_ascii=False, indent=2)}

【出力フォーマット】
マークダウン装飾（```jsonなど）は一切含めず、以下のJSON配列のみを返してください。

[
  {{
    "title": "メインタイトル。【サブタイトル】",
    "slug": "col-unique-slug-here",
    "category": "skincare",
    "system_type": "faq",
    "search_query": "検索用クエリ（例: クレンジング 正しい方法 摩擦）",
    "related_article_slugs": ["best-cleansing-oil"],
    "eyecatch_subject": "sunscreen"
  }}
]
"""
    model = genai.GenerativeModel("models/gemini-flash-lite-latest")
    response = generate_content_with_retry(model, prompt)
    response_text = response.text.strip()
    response_text = re.sub(r'^```json\s*|^```\s*|```$', '', response_text, flags=re.MULTILINE).strip()
    return json.loads(response_text)

def search_google_for_urls(query: str) -> list[str]:
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    }
    url = f"https://www.google.com/search?q={urllib.parse.quote(query)}"
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        if resp.status_code == 200:
            soup = BeautifulSoup(resp.text, 'html.parser')
            urls = []
            for a in soup.find_all('a', href=True):
                href = a['href']
                if href.startswith('/url?q='):
                    actual_url = href.split('/url?q=')[1].split('&')[0]
                    actual_url = urllib.parse.unquote(actual_url)
                    if any(domain in actual_url for domain in ["my-best.com", "michill.jp", "biteki.com", "maquia.hpplus.jp", "mery.jp", "allabout.co.jp"]):
                        urls.append(actual_url)
            return list(dict.fromkeys(urls))
    except Exception as e:
        print(f"⚠️ Google検索エラー: {e}")
    return []

def get_facts_for_theme(theme_info):
    urls = search_google_for_urls(theme_info["search_query"])
    facts = []
    
    from prepare_column import fetch_url_text_requests, fetch_url_text_puppeteer
    
    for url in urls[:2]:
        text = ""
        if "my-best.com" in url:
            text = fetch_url_text_puppeteer(url)
        else:
            text = fetch_url_text_requests(url)
            
        if text and len(text.strip()) > 100:
            import google.generativeai as genai
            prompt = f"""あなたは美容コラムの事実抽出器です。入力されたWeb記事のテキストから、美容・スキンケアに関する客観的事実・知識・手順・メカニズム・注意点・季節要因のみを抽出してください。
            
【抽出する事実の例】
- 洗顔時のすすぎ湯は30〜32度前後のぬるま湯が適している。
- レチノールはシワ改善に効果的だが、紫外線で分解されやすいため夜の使用が推奨される。

【絶対禁止事項】
- 具体的な商品名、ブランド名、メーカー名、店舗名。一切含めないでください。
- ランキング、比較表現、購入誘導。

【出力フォーマット】
マークダウン装飾なしの純粋なJSON。
{{
  "facts": [
    "事実1",
    "事実2"
  ]
}}

【入力テキスト】
{text}
"""
            try:
                model = genai.GenerativeModel("models/gemini-flash-lite-latest")
                response = generate_content_with_retry(model, prompt)
                response_text = response.text.strip()
                response_text = re.sub(r'^```json\s*|^```\s*|```$', '', response_text, flags=re.MULTILINE).strip()
                extracted = json.loads(response_text).get("facts", [])
                facts.extend(extracted)
            except Exception as e:
                print(f"⚠️ 事実抽出失敗 on {url}: {e}")
                
    if not facts:
        print(f"ℹ️ 競合URLからの事実抽出ができなかったため、Geminiによる客観的事実生成にフォールバックします。")
        import google.generativeai as genai
        prompt = f"""あなたは美容皮膚科学およびスキンケア知識の専門家です。
テーマ「{theme_info['title']}」に関して、一般的に美容科学や皮膚科学で認められている、科学的・客観的な事実、メカニズム、正しい手順、注意点、季節要因などを10〜15項目リストアップしてください。

【絶対禁止事項】
- 特定の商品名、ブランド名、メーカー名、店舗名は一切含めないでください（一般名詞のみ）。
- ランキング表現、おすすめ紹介、購入への誘導は一切含めないでください。

【出力フォーマット】
マークダウン装飾なしの純粋なJSON。
{{
  "facts": [
    "事実1",
    "事実2"
  ]
}}
"""
        try:
            model = genai.GenerativeModel("models/gemini-flash-lite-latest")
            response = generate_content_with_retry(model, prompt)
            response_text = response.text.strip()
            response_text = re.sub(r'^```json\s*|^```\s*|```$', '', response_text, flags=re.MULTILINE).strip()
            facts = json.loads(response_text).get("facts", [])
        except Exception as e:
            print(f"❌ フォールバック事実生成失敗: {e}")
            
    return list(set(facts))

def generate_column_draft(theme_info, facts, publish_date):
    import google.generativeai as genai
    
    facts_str = "\n".join([f"- {f}" for f in facts])
    
    schema_path = os.path.join(project_root, "COLUMN_SCHEMA.md")
    rules_path = os.path.join(project_root, "COLUMN_RULES.md")
    
    schema_content = ""
    if os.path.exists(schema_path):
        with open(schema_path, "r", encoding="utf-8") as f:
            schema_content = f.read()
            
    rules_content = ""
    if os.path.exists(rules_path):
        with open(rules_path, "r", encoding="utf-8") as f:
            rules_content = f.read()
    
    prompt = f"""あなたは、仕事も趣味も忙しい美容オタク女子ライターです。
親しみやすく崩したブログ口調で、読者に寄り添うように美容知識コラムを執筆してください。

【コラム生成の絶対ルール】
以下のルールを100%厳密に遵守して執筆してください。特に「商品名の排除」「アフィリエイトリンクの完全禁止」「ですます調の廃止」は絶対です。
{rules_content}

【提供された客観的事実リスト】
これらに基づいて執筆し、科学的に不正確な情報は創作しないでください。
{facts_str}

【メタデータ情報】
- スラグ: {theme_info['slug']}
- タイトル: {theme_info['title']}
- カテゴリ: {theme_info['category']}
- 公開日時: {publish_date}
- 関連比較記事スラグ: {json.dumps(theme_info.get('related_article_slugs', theme_info.get('related_article_slug', [])))}
- アイキャッチ画像パス: /column-images/{theme_info['slug']}.png

【出力JSONスキーマ定義】
出力するJSONは、以下のスキーマ構造に100%適合させてください。
{schema_content}

【出力フォーマット】
マークダウンによるコードブロック装飾（```json や ```）は一切含めず、純粋なJSON文字列のみを返してください。
"""
    model = genai.GenerativeModel("models/gemini-flash-lite-latest")
    response = generate_content_with_retry(model, prompt)
    response_text = response.text.strip()
    response_text = re.sub(r'^```json\s*|^```\s*|```$', '', response_text, flags=re.MULTILINE).strip()
    return response_text

def save_and_validate_draft(draft_json_str):
    draft_path = os.path.join(project_root, "column_draft.json")
    try:
        data = json.loads(draft_json_str)
        with open(draft_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"⚠️ JSONパースエラー: {e}")
        return False, f"JSONパースエラー: {e}"
        
    res = subprocess.run(
        [sys.executable, os.path.join(project_root, "scripts", "validate_column_draft.py")],
        capture_output=True,
        text=True,
        encoding='utf-8'
    )
    if res.returncode == 0:
        return True, ""
    else:
        return False, res.stdout + res.stderr

def fix_draft_with_gemini(theme_info, draft_json_str, error_message):
    import google.generativeai as genai
    
    schema_path = os.path.join(project_root, "COLUMN_SCHEMA.md")
    schema_content = ""
    if os.path.exists(schema_path):
        with open(schema_path, "r", encoding="utf-8") as f:
            schema_content = f.read()
            
    prompt = f"""あなたは美容コラム記事のバリデータエラーを修復するアシスタントです。
生成されたコラムのドラフト JSON に対し、以下のバリデーションエラーが発生しました。
エラー内容を完全に修正した、正しいJSONデータを出力してください。

【バリデーションエラー内容】
{error_message}

【期待される正しいJSONスキーマ構造】
{schema_content}

【元のドラフト JSON】
{draft_json_str}

【修正の注意点】
- `meta.description` は必ず80〜150文字以内にしてください。
- `content.lead` は必ず200〜400文字以内にしてください。
- `content.summary` は必ず200〜300文字以内にしてください。
- `sections` の各要素のキーは必ず `heading`, `body` とし、`point`（任意）にしてください（`title` などに変更しないでください）。
- ` of ` などの日本語破損、不自然な語尾「んだ」は絶対に修正してください。
- アフィリエイトリンクや商品名は絶対に排除してください。

【出力フォーマット】
マークダウン装飾なしの純粋なJSON。
"""
    model = genai.GenerativeModel("models/gemini-flash-lite-latest")
    response = generate_content_with_retry(model, prompt)
    response_text = response.text.strip()
    response_text = re.sub(r'^```json\s*|^```\s*|```$', '', response_text, flags=re.MULTILINE).strip()
    return response_text

def collect_existing_publish_dates():
    dates = set()
    columns_dir = os.path.join(project_root, "src", "content", "columns")
    if os.path.exists(columns_dir):
        for f in os.listdir(columns_dir):
            if f.endswith(".md"):
                path = os.path.join(columns_dir, f)
                try:
                    with open(path, "r", encoding="utf-8") as file:
                        content = file.read()
                        m = re.search(r'^publishDate:\s*["\']?(.*?)["\']?\s*$', content, re.MULTILINE)
                        if m:
                            date_str = m.group(1).strip()
                            if len(date_str) == 10:
                                dates.add(f"{date_str} 12:00:00")
                                dates.add(f"{date_str} 22:00:00")
                            else:
                                dates.add(date_str)
                except Exception as e:
                    print(f"Error reading publish date for {f}: {e}")
                    
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
                            if len(date_str) == 10:
                                dates.add(f"{date_str} 12:00:00")
                                dates.add(f"{date_str} 22:00:00")
                            else:
                                dates.add(date_str)
                except Exception as e:
                    print(f"Error reading publish date for {f}: {e}")
    return dates

def calculate_next_publish_date(existing_dates_set, start_dt, allocated_dates):
    current_dt = start_dt
    while True:
        dt_12 = current_dt.replace(hour=12, minute=0, second=0, microsecond=0)
        if dt_12 > start_dt:
            dt_str = dt_12.strftime("%Y-%m-%d %H:%M:%S")
            if dt_str not in existing_dates_set and dt_str not in allocated_dates:
                return dt_str
                
        dt_22 = current_dt.replace(hour=22, minute=0, second=0, microsecond=0)
        if dt_22 > start_dt:
            dt_str = dt_22.strftime("%Y-%m-%d %H:%M:%S")
            if dt_str not in existing_dates_set and dt_str not in allocated_dates:
                return dt_str
                
        current_dt += datetime.timedelta(days=1)

def main():
    print("🚀 コラム自動生成パイプラインを開始します...")
    
    existing_columns = get_existing_columns()
    existing_articles = get_existing_articles()
    
    now = datetime.datetime.now()
    current_month = now.month
    
    print("⏳ Geminiで重複しないテーマを14件選定中...")
    try:
        themes = select_themes(existing_columns, existing_articles, current_month)
        print(f"✅ 14件のテーマ選定完了。")
    except Exception as e:
        print(f"❌ テーマ選定失敗: {e}")
        sys.exit(1)
        
    existing_dates = collect_existing_publish_dates()
    allocated_dates = []
    
    pending_eyecatches = []
    success_count = 0
    
    for idx, theme in enumerate(themes):
        print(f"\n==================== [{idx+1}/14] {theme['title']} ====================")
        
        # 既に該当スラグのファイルが存在する場合は生成をスキップして進捗を引き継ぐ（レジューム機能）
        columns_dir = os.path.join(project_root, "src", "content", "columns")
        dest_md_path = os.path.join(columns_dir, f"{theme['slug']}.md")
        if os.path.exists(dest_md_path):
            print(f"⏭️ すでにパブリッシュ済みのためスキップします: {theme['slug']}.md")
            success_count += 1
            pending_eyecatches.append({
                "slug": theme["slug"],
                "eyecatch_subject": theme["eyecatch_subject"]
            })
            pub_date = calculate_next_publish_date(existing_dates, now, allocated_dates)
            allocated_dates.append(pub_date)
            continue
            
        pub_date = calculate_next_publish_date(existing_dates, now, allocated_dates)
        allocated_dates.append(pub_date)
        print(f"割り当て公開日時: {pub_date}")
        
        print("⏳ 競合サイトから事実抽出中...")
        facts = get_facts_for_theme(theme)
        print(f"抽出された事実数: {len(facts)}")
        
        print("⏳ コラム本文ドラフトを生成中...")
        draft_str = generate_column_draft(theme, facts, pub_date)
        
        is_ok, err_msg = save_and_validate_draft(draft_str)
        retry_count = 0
        while not is_ok and retry_count < 2:
            retry_count += 1
            print(f"⚠️ バリデーション失敗。自己修復リトライ {retry_count}/2...")
            draft_str = fix_draft_with_gemini(theme, draft_str, err_msg)
            is_ok, err_msg = save_and_validate_draft(draft_str)
            
        if not is_ok:
            print(f"❌ 自己修復に失敗したため、この記事はスキップします: {theme['title']}")
            continue
            
        print("⏳ パブリッシュ中 (Markdown出力)...")
        res = subprocess.run(
            [sys.executable, os.path.join(project_root, "scripts", "publish_column.py")],
            capture_output=True,
            text=True,
            encoding='utf-8'
        )
        if res.returncode == 0:
            print(f"✅ パブリッシュ完了: {theme['slug']}.md")
            success_count += 1
            
            pending_eyecatches.append({
                "slug": theme["slug"],
                "eyecatch_subject": theme["eyecatch_subject"]
            })
        else:
            print(f"❌ パブリッシュ失敗: {res.stderr}")
            
    scratch_dir = os.path.join(project_root, "scratch")
    os.makedirs(scratch_dir, exist_ok=True)
    eyecatch_json_path = os.path.join(scratch_dir, "pending_eyecatches.json")
    with open(eyecatch_json_path, "w", encoding="utf-8") as f:
        json.dump(pending_eyecatches, f, ensure_ascii=False, indent=2)
        
    print(f"\n🎉 パイプライン終了。生成成功: {success_count}/14 本。")
    print(f"画像生成用中間JSONを保存しました: {eyecatch_json_path}")

if __name__ == "__main__":
    main()
