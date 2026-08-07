import os
import sys
import json
import time
import subprocess
import requests
import google.generativeai as genai

# .env.local から環境変数をロード
def load_env():
    env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env.local")
    if not os.path.exists(env_path):
        return
    with open(env_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, val = line.partition("=")
            os.environ[key.strip()] = val.strip()

load_env()

NOTION_API_KEY = os.getenv("NOTION_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
NOTION_DATABASE_ID = "36cddb45-8772-80c3-ab74-eb061ecee73f"

if not NOTION_API_KEY or not GEMINI_API_KEY:
    print("❌ Error: environment variables NOTION_API_KEY or GEMINI_API_KEY are missing.")
    sys.exit(1)

genai.configure(api_key=GEMINI_API_KEY)

NOTION_HEADERS = {
    "Authorization": f"Bearer {NOTION_API_KEY}",
    "Notion-Version": "2022-06-28",
    "Content-Type": "application/json"
}

# 記事生成対象の定義 (UUIDおよびスラッグ・日付・キーワードのマッピング)
targets = [
    {
        "page_id": "399ddb45-8772-816c-b9ed-dfd8bc926ba9",
        "keyword": "クレンジングバーム",
        "slug": "pore-cleansing-balm",
        "date": "2026-07-29 19:00:00",
        "category": "美容・スキンケア"
    },
    {
        "page_id": "399ddb45-8772-813b-9d8c-f40c74487232",
        "keyword": "毛穴クレンジング",
        "slug": "pore-cleansing-oil",
        "date": "2026-07-30 19:00:00",
        "category": "美容・スキンケア"
    },
    {
        "page_id": "399ddb45-8772-81e3-8a69-cf569fae1160",
        "keyword": "美白美容液",
        "slug": "whitening-serum",
        "date": "2026-07-31 19:00:00",
        "category": "美容・スキンケア"
    },
    {
        "page_id": "399ddb45-8772-81ef-bc6e-d56be61a449b",
        "keyword": "エイジングケア洗顔",
        "slug": "aging-care-wash",
        "date": "2026-08-01 19:00:00",
        "category": "美容・スキンケア"
    },
    {
        "page_id": "399ddb45-8772-81c6-8203-e9422c839b25",
        "keyword": "美白クリーム",
        "slug": "whitening-cream",
        "date": "2026-08-02 19:00:00",
        "category": "美容・スキンケア"
    },
    {
        "page_id": "399ddb45-8772-81d4-8f9e-dfa6efe92468",
        "keyword": "朝用美容液",
        "slug": "morning-serum",
        "date": "2026-08-03 19:00:00",
        "category": "美容・スキンケア"
    },
    {
        "page_id": "399ddb45-8772-81d5-ae88-eb2257b2f973",
        "keyword": "日焼け止め",
        "slug": "sunscreen-general",
        "date": "2026-08-04 19:00:00",
        "category": "美容・スキンケア"
    },
    {
        "page_id": "399ddb45-8772-812c-85d7-f7c0c29f0575",
        "keyword": "酵素洗顔",
        "slug": "enzyme-wash",
        "date": "2026-08-05 19:00:00",
        "category": "美容・スキンケア"
    },
    {
        "page_id": "399ddb45-8772-81f4-9985-e236bdeb687d",
        "keyword": "顔用日焼け止め",
        "slug": "face-sunscreen",
        "date": "2026-08-06 19:00:00",
        "category": "美容・スキンケア"
    },
    {
        "page_id": "399ddb45-8772-8110-8063-ef2ac161bdbf",
        "keyword": "リップクリーム",
        "slug": "lip-balm-care",
        "date": "2026-08-07 19:00:00",
        "category": "美容・スキンケア"
    }
]

def update_status(page_id, status):
    url = f"https://api.notion.com/v1/pages/{page_id}"
    payload = {
        "properties": {
            "Status": {
                "status": {"name": status}
            }
        }
    }
    try:
        res = requests.patch(url, headers=NOTION_HEADERS, json=payload, timeout=15)
        return res.status_code == 200
    except Exception as e:
        print(f"⚠️ Failed to update Notion status for page {page_id}: {e}")
        return False

def generate_draft_with_gemini(keyword, products, feedback_msg=None):
    models_to_try = [
        "models/gemini-2.0-flash",
        "models/gemini-2.5-flash",
        "models/gemini-flash-latest",
        "models/gemini-flash-lite-latest"
    ]
    
    products_fact_text = ""
    for idx, p in enumerate(products):
        products_fact_text += f"\n### 商品{idx+1}: {p['name']}\n"
        products_fact_text += f"- facts: {', '.join(p.get('facts', []))}\n"
        products_fact_text += f"- unique_points: {', '.join(p.get('unique_points', []))}\n"
        products_fact_text += f"- free_from: {', '.join(p.get('free_from', []))}\n"
        products_fact_text += f"- recommended_for: {', '.join(p.get('recommended_for', []))}\n"
        
    prompt = f"""あなたは客観的な事実のみに基づき、美容・スキンケア商品の紹介記事を作成するデータ変換器です。
指定されたJSONスキーマに従い、日本語で高品質な紹介記事のドラフトを生成してください。

【制約事項（絶対遵守）】
1. 事実情報（facts, unique_points, free_from, recommended_for）のみを元に執筆してください。そこに含まれない成分、効果効能、仕様、特徴を推測したり追加したりすることは禁止します。
2. 以下の禁止語を文章（タイトル、本文、説明、Pros/Cons含む）から完全に排除してください：
   - "最強", "神", "圧倒的", "超おすすめ", "おすすめ", "ぴったり", "最適", "心強い", "頼もしい", "納得", "魅力", "味方", "パートナー", "相棒"
3. 語尾は「です」「ます」調とし、「〜だよ」「〜だね」「〜んだ」などのくだけた口語表現は禁止します。
4. 単調なリズムを避けるため、「かも」「てね」「！」のいずれかを、記事全体（intro, summary, descriptions）のどこかで最低1回は使用してください。ただし多用は避けてください。
5. 日本語破損表現の「 of 」（例：「〜 of 〜」などの英語表記）を絶対に出力しないでください。
6. descriptions や Pros/Cons、ポイントに感情的・精神的な抽象表現（例：「自分へのご褒表」「丁寧な暮らし」「きれいを諦めない」など）で文字数を埋めず、客観的仕様や処方を中心に記述してください。
7. 重複する表現やフレーズ（15文字以上）が、異なる商品の説明文や導入・まとめ等で3回以上重複出現しないように、語彙や文体構成をバラけさせてください。
8. 以下の製品説明の書き出しパターンは、製品定義文に収束してしまうため、避けてください：
   - 「〜を配合した、〜な製品です。」のような文。
   - 「〜です。」という短い説明から始めないでください。

【JSONスキーマ】
{{
  "meta": {{
    "title": "記事タイトル（魅力的で客観的なタイトル）",
    "excerpt": "80〜150文字のメタディスクリプション用抜粋（文字数厳守）"
  }},
  "content": {{
    "intro": "320〜450文字の導入文（文字数厳守）",
    "summary": "260〜350文字のまとめ文（文字数厳守）"
  }},
  "ui": {{
    "points": ["選び方のポイント1（1項目1文、20文字程度、最大3項目）", "ポイント2", "ポイント3"],
    "faq": [
      {{
        "question": "よくある質問Q1（factsで回答可能な内容、1〜3問、無理に3問埋めない）",
        "answer": "回答A1（factsに基づく客観的な回答）"
      }}
    ]
  }},
  "products": [
    {{
      "name": "商品名（インプットと完全に一致させること）",
      "description": "商品説明（150〜350文字厳守。必ず商品名を1回以上含め、具体的な事実・数値・成分名を1つ以上含める）",
      "analysis": {{
        "pros": ["メリット1（factsに基づく客観的な強み、1項目1文、2〜3項目）", "メリット2"],
        "cons": ["デメリット1（factsに基づく客観的な注意点、1〜2項目。事実から導けない場合は「特に気になるところは見当たりません」と記述し、'該当情報なし'などの機械的表現は禁止）"],
        "recommended_for": ["こんな人におすすめ1（インプットのrecommended_forをベースにする）"]
      }}
    }}
  ]
}}

【対象商品情報（キーワード: {keyword}）】
{products_fact_text}
"""

    if feedback_msg:
        prompt += f"""
【重要: 前回のバリデーションエラーに対する修正指示】
前回の生成結果は以下のエラーでバリデーションに失敗しました。今回の生成ではこれらのエラーを完全に修正してください：
{feedback_msg}
"""

    last_err = None
    for model_name in models_to_try:
        try:
            print(f"Trying Gemini model: {model_name}...")
            model = genai.GenerativeModel(model_name)
            response = model.generate_content(
                prompt,
                generation_config={
                    "response_mime_type": "application/json",
                    "temperature": 0.2
                }
            )
            data = json.loads(response.text.strip())
            return data
        except Exception as e:
            last_err = e
            print(f"⚠️ Error or Quota for model {model_name}: {e}. Waiting 15s...")
            time.sleep(15)
            
    print(f"❌ All models failed to generate draft: {last_err}")
    return None

def run_validation(relaxed=False):
    cmd = ["python3", "scripts/validate_article_draft.py"]
    if relaxed:
        cmd.append("--relaxed")
    res = subprocess.run(cmd, capture_output=True, text=True)
    return res.returncode == 0, res.stdout + "\n" + res.stderr

def main():
    stockpile_path = "scripts/stockpile_data.json"
    
    print(f"🏁 Starting safe batch article generation for {len(targets)} targets.")
    
    for idx, target in enumerate(targets):
        page_id = target["page_id"]
        keyword = target["keyword"]
        slug = target["slug"]
        date = target["date"]
        category = target["category"]
        
        print("\n" + "="*80)
        print(f"🔄 [{idx+1}/{len(targets)}] Processing: {keyword} ({slug})")
        print("="*80)
        
        # 1. 安全対策: 古い stockpile_data.json のクリーンアップ
        if os.path.exists(stockpile_path):
            print("🧹 Cleaning up old stockpile_data.json to prevent cached data pollution...")
            os.remove(stockpile_path)
            
        # Notion ステータスを「進行中」に設定
        print("Notionステータスを「進行中」に設定します...")
        update_status(page_id, "進行中")
        
        # 2. prepare_stockpile.py の実行
        print(f"Running prepare_stockpile.py (ID: {page_id})...")
        p_res = subprocess.run(["python3", "scripts/prepare_stockpile.py", page_id], capture_output=True, text=True)
        
        if p_res.returncode != 0:
            print(f"❌ prepare_stockpile.py failed with exit code: {p_res.returncode}")
            print(f"Stdout:\n{p_res.stdout}\nStderr:\n{p_res.stderr}")
            update_status(page_id, "エラー")
            continue
            
        # 3. stockpile_data.json の存在＆有効性検証
        if not os.path.exists(stockpile_path):
            print("❌ Error: prepare_stockpile.py finished but stockpile_data.json was not created.")
            update_status(page_id, "エラー")
            continue
            
        try:
            with open(stockpile_path, "r", encoding="utf-8") as f:
                stock_data = json.load(f)
        except Exception as e:
            print(f"❌ Failed to parse generated stockpile_data.json: {e}")
            update_status(page_id, "エラー")
            continue
            
        products = stock_data.get("products", [])
        
        # 重複排除ロジック
        seen_names = set()
        unique_products = []
        for p in products:
            p_name = p.get("name", "").strip()
            if not p_name:
                continue
            if p_name not in seen_names:
                seen_names.add(p_name)
                unique_products.append(p)
                
        if len(unique_products) < 6:
            print(f"❌ Error: Unique products count is less than 6 (found: {len(unique_products)}) after deduplication.")
            update_status(page_id, "エラー")
            continue
            
        target_products = unique_products[:6]
        
        # 4. Gemini ドラフト生成 & バリデーション (最大5回試行)
        draft_ok = False
        draft_data = None
        feedback_msg = None
        
        for attempt in range(5):
            print(f"Gemini で記事ドラフトを生成中 (試行: {attempt+1}/5)...")
            draft_data = generate_draft_with_gemini(keyword, target_products, feedback_msg)
            if not draft_data:
                print("⚠️ Draft generation failed. Retrying...")
                time.sleep(5)
                continue
                
            # ドラフトを一時ファイルに書き出す
            with open("article_draft.json", "w", encoding="utf-8") as df:
                json.dump(draft_data, df, ensure_ascii=False, indent=2)
                
            # バリデーション実行（最終試行時には relaxed 緩和モードを許可）
            use_relaxed = (attempt == 4)
            ok, err_msg = run_validation(relaxed=use_relaxed)
            if ok:
                if use_relaxed:
                    print("✅ Validation passed (RELAXED mode).")
                else:
                    print("✅ Validation passed.")
                draft_ok = True
                break
            else:
                print(f"⚠️ Validation failed:\n{err_msg}")
                feedback_msg = err_msg
                time.sleep(2)
                
        if not draft_ok:
            print(f"❌ Failed to generate valid draft for {keyword} after 5 attempts. Skipping.")
            update_status(page_id, "エラー")
            continue
            
        # 5. publish_article.py の実行
        title = draft_data["meta"]["title"]
        date_prefix = date.split(" ")[0].replace("-", "")
        forced_slug = f"{date_prefix}-{slug}"
        
        print(f"Running publish_article.py (title: {title}, slug: {forced_slug})...")
        pub_cmd = [
            "python3", "scripts/publish_article.py",
            "--title", title,
            "--category", category,
            "--slug", forced_slug,
            "--date", date
        ]
        if attempt == 4:
            pub_cmd.append("--relaxed")
            
        pub_res = subprocess.run(pub_cmd, capture_output=True, text=True)
        if pub_res.returncode != 0:
            print(f"❌ publish_article.py failed with exit code: {pub_res.returncode}")
            print(f"Stdout:\n{pub_res.stdout}\nStderr:\n{pub_res.stderr}")
            update_status(page_id, "エラー")
            continue
            
        print(f"🎉 Successfully published article: {forced_slug}")
        update_status(page_id, "完了")
        
        # クールダウン待機
        print("⏳ Sleeping 20s before starting next article...")
        time.sleep(20)
        
    print("\n🏁 Safely completed batch article generation!")

if __name__ == "__main__":
    main()
