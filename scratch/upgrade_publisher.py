import os
import re

def main():
    filepath = "scripts/publish_article.py"
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    # 1. Update ARTICLE_SCHEMA
    old_schema = """ARTICLE_SCHEMA = {
    "type": "object",
    "properties": {
        "excerpt": {"type": "string"},
        "intro": {"type": "string"},
        "points": {
            "type": "array",
            "items": {"type": "string"}
        },
        "products": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "description": {"type": "string"},
                    "recommended_for": {
                        "type": "array",
                        "items": {"type": "string"}
                    }
                },
                "required": ["name", "description", "recommended_for"]
            }
        },
        "summary": {"type": "string"}
    },
    "required": ["excerpt", "intro", "points", "products", "summary"]
}"""

    new_schema = """ARTICLE_SCHEMA = {
    "type": "object",
    "properties": {
        "title": {"type": "string"},
        "excerpt": {"type": "string"},
        "intro": {"type": "string"},
        "points": {
            "type": "array",
            "items": {"type": "string"}
        },
        "products": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "description": {"type": "string"},
                    "recommended_for": {
                        "type": "array",
                        "items": {"type": "string"}
                    }
                },
                "required": ["name", "description", "recommended_for"]
            }
        },
        "summary": {"type": "string"}
    },
    "required": ["title", "excerpt", "intro", "points", "products", "summary"]
}"""

    if old_schema in content:
        content = content.replace(old_schema, new_schema)
        print("✅ Upgraded ARTICLE_SCHEMA")
    else:
        print("❌ Could not find ARTICLE_SCHEMA")

    # 2. Update get_notion_data
    old_get_notion_data = """def get_notion_data(article_title: str):
    script_dir = os.path.dirname(os.path.abspath(__file__))
    stockpile_path = os.path.join(script_dir, "stockpile_data.json")
    
    if not os.path.exists(stockpile_path):
        print(f"❌ Error: stockpile_data.json not found at {stockpile_path}")
        return []
        
    try:
        with open(stockpile_path, 'r', encoding='utf-8') as f:
            stockpile_data = json.load(f)
    except Exception as e:
        print(f"❌ Error reading stockpile_data.json: {e}")
        return []
        
    json_title = stockpile_data.get("default_title", "")
    print(f"📖 Loaded local stockpile data for article: '{json_title}'")
    if article_title.strip() != json_title.strip():
        print(f"⚠️ Warning: Requested article_title '{article_title}' does not exactly match default_title '{json_title}' in stockpile_data.json.")
        
    products = []
    category = stockpile_data.get("default_category", "ガジェット")
    json_products = stockpile_data.get("products", [])
    
    for i, p in enumerate(json_products):
        resolved = p.get("resolved_details", {})
        
        # Clean product name: remove newlines or extra spaces
        raw_name = p.get("original_name", "")
        clean_name = re.sub(r'\\s+', ' ', raw_name).strip()
        
        # We also need an ID
        item_id = p.get("id") or f"stockpile_{p.get('rank', i + 1)}"
        
        products.append({
            "id": item_id,
            "name": clean_name,
            "image_url": resolved.get("image_url") or "",
            "amazon_url": resolved.get("amazon_url") or "",
            "rakuten_url": clean_rakuten_url(resolved.get("rakuten_url") or ""),
            "yahoo_url": clean_yahoo_url(resolved.get("yahoo_url") or "", clean_name),
            "amazon_price": str(resolved.get("amazon_price", "なし")),
            "rakuten_price": str(resolved.get("rakuten_price", "なし")),
            "yahoo_price": str(resolved.get("yahoo_price", "なし")),
            "category": category
        })
    return products"""

    new_get_notion_data = """def get_notion_data():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    stockpile_path = os.path.join(script_dir, "stockpile_data.json")
    
    if not os.path.exists(stockpile_path):
        print(f"❌ Error: stockpile_data.json not found at {stockpile_path}")
        return []
        
    try:
        with open(stockpile_path, 'r', encoding='utf-8') as f:
            stockpile_data = json.load(f)
    except Exception as e:
        print(f"❌ Error reading stockpile_data.json: {e}")
        return []
        
    products = []
    category = stockpile_data.get("default_category", "ガジェット")
    json_products = stockpile_data.get("products", [])
    
    for i, p in enumerate(json_products):
        resolved = p.get("resolved_details", {})
        
        # Clean product name: remove newlines or extra spaces
        raw_name = p.get("original_name", "")
        clean_name = re.sub(r'\\s+', ' ', raw_name).strip()
        
        # We also need an ID
        item_id = p.get("id") or f"stockpile_{p.get('rank', i + 1)}"
        
        products.append({
            "id": item_id,
            "name": clean_name,
            "image_url": resolved.get("image_url") or "",
            "amazon_url": resolved.get("amazon_url") or "",
            "rakuten_url": clean_rakuten_url(resolved.get("rakuten_url") or ""),
            "yahoo_url": clean_yahoo_url(resolved.get("yahoo_url") or "", clean_name),
            "amazon_price": str(resolved.get("amazon_price", "なし")),
            "rakuten_price": str(resolved.get("rakuten_price", "なし")),
            "yahoo_price": str(resolved.get("yahoo_price", "なし")),
            "category": category,
            "competitor_description": p.get("competitor_description", "")
        })
    return products"""

    # We need to normalize newlines to make sure they match
    norm_content = content.replace("\r\n", "\n")
    norm_old_get_notion_data = old_get_notion_data.replace("\r\n", "\n")
    
    if norm_old_get_notion_data in norm_content:
        norm_content = norm_content.replace(norm_old_get_notion_data, new_get_notion_data)
        print("✅ Upgraded get_notion_data")
    else:
        # Try a substring match to see why it fails
        print("❌ Could not find get_notion_data exactly")
        # Direct replacement using regex or manual lookup
        start_idx = norm_content.find("def get_notion_data")
        end_idx = norm_content.find("def generate_content_with_llm")
        if start_idx != -1 and end_idx != -1:
            norm_content = norm_content[:start_idx] + new_get_notion_data + "\n\n" + norm_content[end_idx:]
            print("✅ Upgraded get_notion_data using block index")

    # 3. Update generate_content_with_llm
    new_generate_content_with_llm = """def generate_content_with_llm(stockpile_data):
    rules_text = load_generation_rules()
    rules_section = f"\\n\\n【記事生成ルール（必ず遵守）】\\n{rules_text}" if rules_text else ""

    products_input = []
    for p in stockpile_data.get("products", []):
        products_input.append({
            "name": p.get("original_name", ""),
            "competitor_description": p.get("competitor_description", "")
        })

    prompt = f\"\"\"あなたはプロのWebライターとして、中立的かつ信頼性の高い商品紹介記事を執筆してください。
読者に親しみやすさを感じさせつつも、過度な装飾やAI特有の極端な表現を避けた、誠実なトーンを維持してください。
{rules_section}

【インプット情報（競合サイトのデータ）】
■ 競合記事タイトル: {stockpile_data.get("competitor_title", "")}
■ 競合イントロ文: {stockpile_data.get("competitor_intro", "")}
■ 競合の「選び方のポイント」: {stockpile_data.get("competitor_buying_guide", "")}

■ 紹介する商品リストおよび競合の商品説明（これをベースにGENERATION_RULESに従ってアレンジ・再構成してください）:
{json.dumps(products_input, ensure_ascii=False, indent=2)}

【厳守事項】
0. **本記事は【🌸 A. 並列（Parallel）モード】で作成します。**
1. **ランキング形式の禁止**: 全ての商品を「おすすめの選択肢」として並列に扱ってください。順位や「第○位」という表現は一切使わないでください。
2. **NGワード**: 「マジで」「ヤバい」「神アイテム」「最高」「究極」などの煽り文句や、過剰な強調表現は使用禁止です。
3. **一人称の禁止**: 「おこげ」「私」「僕」「筆者」などの一人称、および個人の体験談を装った記述はすべて削除してください。
4. **商品説明の制限**: 各商品の紹介（description）は、**必ず1000文字以上**で詳細に記述してください。競合の商品説明（competitor_description）の具体的な特徴やメリットをベースにし、コピペではなく、独自の表現で1000文字以上のリッチなコンテンツに書き直してください。（出力上限内に収めるため、1200〜1500文字程度を目安とし、1800文字を超えないよう調整してください）
5. **絵文字の活用**: 各見出しおよび商品説明において、絵文字は**1商品につき1〜2個まで**に制限してください。さらに、商品の仕様（フルスペクトル、クリップ、調光など）に完全に適合した実用アイコンのみを使用し、抽象的な無関係な絵文字は含めないでください。
6. **ターゲット層**: 各商品に対し、「こんな人におすすめ！」という項目で、具体的な推奨理由を**3つの箇条書き**で作成してください。
7. **変数名禁止**: YAHOO_PRICE・RAKUTEN_PRICE・AMAZON_PRICE・YAHOOなどの変数名を文中に絶対に含めないでください。
8. **段落分け**: 各段落は**1〜2文程度**とし、段落間には空行（\\\\n\\\\n）を入れてスマホで最も読みやすい構成にしてください。また、文章が長く繋がらないように配慮してください。
9. **記事タイトル自動生成**:
   - 競合記事タイトルを参考に、GENERATION_RULESに定められた【情緒 × 機能の二段構え】の美しいタイトルを自動生成してください。
   - 禁止ワード（「おすすめ〇選」「人気〇選」「ランキング」「比較」「2024」「2026」など）は絶対に使用しないでください。
   - タイトルは次の形式にしてください: `[情緒的なメインタイトル]。【[機能的なサブタイトル]6選】` (必ず full-width period `。` を入れ、最後は `6選】` で終わるようにしてください)

出力形式: JSONスキーマに完全に従ってください。\"\"\"
    
    model = genai.GenerativeModel('models/gemini-2.5-flash')
    res = model.generate_content(
        prompt,
        generation_config=genai.types.GenerationConfig(
            temperature=0.6,
            max_output_tokens=8192,
            response_mime_type="application/json",
            response_schema=ARTICLE_SCHEMA
        )
    )
    return res.text if res else None"""

    start_idx = norm_content.find("def generate_content_with_llm")
    end_idx = norm_content.find("def truncate_product_name")
    if start_idx != -1 and end_idx != -1:
        norm_content = norm_content[:start_idx] + new_generate_content_with_llm + "\n\n" + norm_content[end_idx:]
        print("✅ Upgraded generate_content_with_llm")
    else:
        print("❌ Could not find generate_content_with_llm block index")

    # 4. Update run_publish
    new_run_publish = """def run_publish(article_title: str = None, category: str = None, slug: str = None):
    print("🚀 Running article generator...")
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    stockpile_path = os.path.join(script_dir, "stockpile_data.json")
    
    if not os.path.exists(stockpile_path):
        print(f"❌ Error: stockpile_data.json not found at {stockpile_path}")
        return False
        
    try:
        with open(stockpile_path, 'r', encoding='utf-8') as f:
            stockpile_data = json.load(f)
    except Exception as e:
        print(f"❌ Error reading stockpile_data.json: {e}")
        return False
        
    products = get_notion_data()
    if not products: 
        print("❌ No products retrieved from stockpile data.")
        return False
        
    # Limit to top 6
    products = products[:6]
    category = category or stockpile_data.get("default_category", "ガジェット")
    
    raw = generate_content_with_llm(stockpile_data)
    if not raw: 
        print("❌ LLM content generation failed.")
        return False
        
    data = json.loads(raw)
    generated_title = data.get("title", "").strip()
    
    if not generated_title:
        generated_title = stockpile_data.get("default_title", "無題の記事")
        
    output_title = generated_title.replace("2024", "2026")
    slug = slug or slugify(output_title)
    
    # PR開示を先頭に1回だけ配置（frontmatter直後の本文の最初）
    intro_text = data['intro']
    # 念のため intro_text からPR開示の重複を除去
    intro_text = intro_text.replace(PR_DISCLOSURE, "").strip()

    # 変数名クリーニング（LLMが出力してしまった場合に備えて）
    intro_text = clean_variable_names(intro_text)
    for p in data['products']:
        p['description'] = clean_variable_names(p['description'])
    # 念のため summary からPR開示の重複を除去
    summary_clean = data['summary'].replace(PR_DISCLOSURE, "").strip()
    summary_clean = re.sub(r'<p class="pr-disclosure">.*?</p>', '', summary_clean).strip()
    data['summary'] = clean_variable_names(summary_clean)

    markdown = (
        f'--- \\n'
        f'title: "{output_title}"\\n'
        f'coverImage: ""\\n'
        f'excerpt: "{data["excerpt"]}"\\n'
        f'publishDate: "{datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).strftime("%Y-%m-%d")}"\\n'
        f'category: "{category}"\\n'
        f'---\\n\\n'
        f'{intro_text}\\n\\n'
        f'## ✅ 選び方のポイント\\n<ul>'
        + "".join([f"<li>{p}</li>" for p in data['points']])
        + "</ul>\\n\\n"
    )

    for i, p in enumerate(data['products']):
        notion_p = next((x for x in products if x['name'].lower() in p['name'].lower() or p['name'].lower() in x['name'].lower()), None)
        display_name = truncate_product_name(p['name'])
        markdown += f"### 🌸 {display_name}\\n"
        if notion_p and notion_p['image_url']: markdown += f"IMAGE: {notion_p['image_url']}\\n"
        
        if notion_p:
            for platform in ['amazon', 'rakuten', 'yahoo']:
                price = notion_p.get(f'{platform}_price')
                if price and price != "なし": markdown += f"{platform.upper()}_PRICE: {price}\\n"
            for platform, key in [('amazon', 'asin'), ('rakuten', 'rakuten'), ('yahoo', 'yahoo')]:
                url = notion_p.get(f'{platform}_url')
                if url: markdown += f"{key.upper()}: {url}\\n"
        
        # ★商品画像・アフィリエイト定義の直後（購入ボタンの1セットめ）
        markdown += f"\\n[AMAZON_LINK_HERE] [RAKUTEN_LINK_HERE] [YAHOO_LINK_HERE]\\n\\n"

        # 説明文のフォーマット（1000文字以上）
        formatted_desc = p['description'].replace('\\\\n', '\\n')
        markdown += f"{formatted_desc}\\n\\n"
        
        # ★説明文の下（購入ボタンの2セットめ）
        markdown += f"[AMAZON_LINK_HERE] [RAKUTEN_LINK_HERE] [YAHOO_LINK_HERE]\\n\\n"
        
        # 「こんな人におすすめ！」箇条書きの追加
        markdown += f"👤 **こんな人におすすめ！**\\n"
        markdown += "\\n".join([f"- {item}" for item in p['recommended_for']]) + "\\n\\n"
    
    markdown += f"## 💬 まとめ\\n{data['summary']}\\n\\n"
    markdown += f'<p class="pr-disclosure">{PR_DISCLOSURE}</p>\\n'

    path = f"src/content/articles/{slug}.md"
    with open(path, 'w', encoding='utf-8') as f: f.write(markdown)
    
    # アイキャッチ生成
    image_urls = [p['image_url'] for p in products if p.get('image_url')]
    generate_eyecatch_html(slug, output_title, category, image_urls, get_seasonal_catch_copy(category))
    take_eyecatch_screenshot(slug)
    return True"""

    start_idx = norm_content.find("def run_publish")
    end_idx = norm_content.find("import argparse")
    if start_idx != -1 and end_idx != -1:
        norm_content = norm_content[:start_idx] + new_run_publish + "\n\n" + norm_content[end_idx:]
        print("✅ Upgraded run_publish")
    else:
        print("❌ Could not find run_publish block index")

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(norm_content)
    print("🎉 All publisher upgrades successfully written in clean UTF-8!")

if __name__ == "__main__":
    main()
