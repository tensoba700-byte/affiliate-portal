import os

def main():
    filepath = "scripts/publish_article.py"
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    # Define schemas to add at the top
    schemas_def = """HEADER_SCHEMA = {
    "type": "object",
    "properties": {
        "title": {"type": "string"},
        "excerpt": {"type": "string"},
        "intro": {"type": "string"},
        "points": {
            "type": "array",
            "items": {"type": "string"}
        }
    },
    "required": ["title", "excerpt", "intro", "points"]
}

PRODUCT_SCHEMA = {
    "type": "object",
    "properties": {
        "description": {"type": "string"},
        "recommended_for": {
            "type": "array",
            "items": {"type": "string"}
        }
    },
    "required": ["description", "recommended_for"]
}

SUMMARY_SCHEMA = {
    "type": "object",
    "properties": {
        "summary": {"type": "string"}
    },
    "required": ["summary"]
}"""

    # Insert schemas_def after ARTICLE_SCHEMA definition
    # Find the end of ARTICLE_SCHEMA or just place it before CATEGORY_THEMES
    target_idx = content.find("# ----- Category Theme System -----")
    if target_idx != -1:
        content = content[:target_idx] + schemas_def + "\n\n" + content[target_idx:]
        print("✅ Added HEADER_SCHEMA, PRODUCT_SCHEMA, SUMMARY_SCHEMA definitions")

    # Define the new split generate_content_with_llm
    new_generate_content_with_llm = """def generate_content_with_llm(stockpile_data):
    rules_text = load_generation_rules()
    rules_section = f"\\n\\n【記事生成ルール（必ず遵守）】\\n{rules_text}" if rules_text else ""
    
    model = genai.GenerativeModel('models/gemini-2.5-flash')
    
    # 1. Generate Header Info
    print("🚀 Generating Header (Title, Excerpt, Intro, Points)...")
    header_prompt = f\"\"\"あなたはプロのWebライターとして、中立的かつ信頼性の高い商品紹介記事を執筆してください。
{rules_section}

【インプット情報（競合サイトのデータ）】
■ 競合記事タイトル: {stockpile_data.get("competitor_title", "")}
■ 競合イントロ文: {stockpile_data.get("competitor_intro", "")}
■ 競合の「選び方のポイント」: {stockpile_data.get("competitor_buying_guide", "")}

【厳守事項】
- 記事タイトル自動生成:
  * 競合記事タイトルを参考に、GENERATION_RULESに定められた【情緒 × 機能の二段構え】の美しいタイトルを自動生成してください。
  * 禁止ワード（「おすすめ〇選」「人気〇選」「ランキング」「比較」「2024」「2026」など）は絶対に使用しないでください。
  * タイトルは次の形式にしてください: `[情緒的なメインタイトル]。【[機能的なサブタイトル]6選】` (必ず full-width period `。` を入れ、最後は `6選】` で終わるようにしてください)
- 導入文（intro）:
  * 競合のイントロ文を参考に、読者に優しく寄り添うトーンでオリジナルの魅力的な導入文を作成してください。段落間には空行（\\n\\n）を入れてください。
- 選び方のポイント（points）:
  * 競合の「選び方のポイント」および商品特徴を参考に、3つの具体的なポイントをリスト形式で出力してください。

出力形式: JSONスキーマに完全に従ってください。\"\"\"

    header_res = model.generate_content(
        header_prompt,
        generation_config=genai.types.GenerationConfig(
            temperature=0.3,
            response_mime_type="application/json",
            response_schema=HEADER_SCHEMA
        )
    )
    header_data = json.loads(header_res.text)
    print("✅ Header generated! Title:", header_data.get("title"))

    # 2. Generate Products Info in Loop
    generated_products = []
    for idx, p in enumerate(stockpile_data.get("products", [])[:6], 1):
        print(f"🚀 Generating Product {idx}/6: {p.get('original_name')}...")
        product_prompt = f\"\"\"あなたはプロのWebライターとして、特定の商品紹介文を執筆してください。
{rules_section}

【インプット情報】
■ 対象商品名: {p.get('original_name')}
■ 競合の商品説明（これをベースにGENERATION_RULESに従ってアレンジ・再構成してください）:
{p.get('competitor_description')}

【厳守事項】
1. **商品説明の制限**:
   - 紹介文（description）は、**必ず1000文字以上**で極めて詳細に記述してください。コピペではなく、特徴・使用感・他製品と比較したメリットを独自の美しい表現で書き直してください。（1000〜1200文字程度を目安とし、1500文字を超えないよう調整してください）
   - 各段落は**1〜2文程度（極めて短く）**とし、段落間には必ず**空行（\\n\\n）**を挿入してください。スマホでの読みやすさを最優先にしてください。
2. **NGワード**: 「マジで」「ヤバい」「神アイテム」「最高」「究極」などの煽り文句や、過剰な強調表現は使用禁止です。
3. **一人称の禁止**: 一人称や個人の体験談を装った記述はすべて削除してください。
4. **絵文字の活用**: 絵文字は**全体で1〜2個まで**に制限し、商品の具体的な仕様に完全に適合した実用アイコンのみを使用してください。
5. **変数名禁止**: YAHOO_PRICE・RAKUTEN_PRICE・AMAZON_PRICE・YAHOOなどの変数名を文中に絶対に含めないでください。
6. **ターゲット層**: 「こんな人におすすめ！」の箇条書きに含める具体的な推奨理由を**3つ**作成してください。

出力形式: JSONスキーマに完全に従ってください。\"\"\"

        product_res = model.generate_content(
            product_prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=0.3,
                response_mime_type="application/json",
                response_schema=PRODUCT_SCHEMA
            )
        )
        product_data = json.loads(product_res.text)
        print(f"  -> Generated! Desc length: {len(product_data.get('description'))} characters.")
        generated_products.append({
            "name": p.get("original_name"),
            "description": product_data.get("description"),
            "recommended_for": product_data.get("recommended_for")
        })

    # 3. Generate Summary
    print("🚀 Generating Summary...")
    summary_prompt = f\"\"\"あなたはプロのWebライターとして、紹介記事の「まとめ」セクションを執筆してください。
{rules_section}

【厳守事項】
- 優しく寄り添うトーンで、記事全体の要約と読者の背中を押すまとめ文（summary）を作成してください。
- 各段落は1〜2文程度とし、段落間には空行（\\n\\n）を入れてください。
- PR開示文（アフィリエイト広告を含みますなど）はシステム側で自動挿入するため、文中に絶対に含めないでください。

出力形式: JSONスキーマに完全に従ってください。\"\"\"

    summary_res = model.generate_content(
        summary_prompt,
        generation_config=genai.types.GenerationConfig(
            temperature=0.3,
            response_mime_type="application/json",
            response_schema=SUMMARY_SCHEMA
        )
    )
    summary_data = json.loads(summary_res.text)
    print("✅ Summary generated!")

    # Combine into unified JSON structure compatible with rest of publisher
    final_article = {
        "title": header_data.get("title"),
        "excerpt": header_data.get("excerpt"),
        "intro": header_data.get("intro"),
        "points": header_data.get("points"),
        "products": generated_products,
        "summary": summary_data.get("summary")
    }
    return json.dumps(final_article, ensure_ascii=False)"""

    start_idx = content.find("def generate_content_with_llm")
    end_idx = content.find("def truncate_product_name")
    if start_idx != -1 and end_idx != -1:
        content = content[:start_idx] + new_generate_content_with_llm + "\n\n" + content[end_idx:]
        print("✅ Upgraded generate_content_with_llm to split implementation")
    else:
        print("❌ Could not find generate_content_with_llm block index")

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)
    print("🎉 Split publisher successfully upgraded!")

if __name__ == "__main__":
    main()
