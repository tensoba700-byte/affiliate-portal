import os

def main():
    filepath = "scripts/publish_article.py"
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    # 1. Remove google.generativeai import
    content = content.replace("import google.generativeai as genai", "")

    # 2. Define static generate_content_static instead of generate_content_with_llm
    new_generate_content = """def generate_content_with_llm(stockpile_data):
    competitor_title = stockpile_data.get("competitor_title", "水草育成LEDライトのおすすめ人気ランキング")
    
    # 3-line format headline: [Emotional Main Title]。【[Functional Subtitle]6選】
    # Example: 水槽に、生命の輝きを。【水草を育むLED照明6選】
    title = "水槽に、生命の輝きを。【水草を育むLED照明6選】"
    
    excerpt = "水草の光合成を促し、美しいアクアリウムを実現するための水草育成LEDライト。選び方のポイントや、人気おすすめ商品6選を詳しくご紹介します。"
    
    intro = stockpile_data.get("competitor_intro", "")
    if not intro:
        intro = "水槽内の水草を美しく育てるために欠かせない「水草育成LEDライト」。さまざまな製品があり、どれを選ぶべきか迷ってしまいますよね。\\n\\n今回は、人気のおすすめ商品を詳しくご紹介します。ぜひ参考にしてください！"
        
    points = [
        "水草の光合成に有効な波長（青色・赤色）が強化されているか確認しましょう。",
        "水槽のサイズや形状（フレームレス、枠あり）に適合する設置方法を選びましょう。",
        "調光機能やタイマー機能など、利便性を高める付加機能にも注目しましょう。"
    ]
    
    products = []
    for p in stockpile_data.get("products", []):
        desc = p.get("competitor_description", "")
        # Clean double newlines if any
        desc = desc.replace("\\n", "\\n\\n")
        
        products.append({
            "name": p.get("original_name", ""),
            "description": desc,
            "recommended_for": [
                "水草の育成効果が高く、信頼性の高いライトを求める人",
                "水槽全体の美観を高めるスリムなデザインを好む人",
                "明るさ調整やタイマー機能をスマートに使いこなしたい人"
            ]
        })
        
    summary = "水草育成LEDライトは、水槽内の美しい水景と健康的な生態系を維持するために不可欠なアイテムです。それぞれの製品の特徴や調光機能を比較し、ご自身の水槽環境に最適な1本を見つけてみてください。"
    
    final_article = {
        "title": title,
        "excerpt": excerpt,
        "intro": intro,
        "points": points,
        "products": products,
        "summary": summary
    }
    return json.dumps(final_article, ensure_ascii=False)"""

    start_idx = content.find("def generate_content_with_llm")
    end_idx = content.find("def truncate_product_name")
    if start_idx != -1 and end_idx != -1:
        content = content[:start_idx] + new_generate_content + "\n\n" + content[end_idx:]
        print("✅ Replaced generate_content_with_llm with static implementation")
    else:
        print("❌ Could not find generate_content_with_llm block index")

    # Remove the schemas if present since they are no longer needed
    content = content.replace("HEADER_SCHEMA = {", "# HEADER_SCHEMA = {")
    content = content.replace("PRODUCT_SCHEMA = {", "# PRODUCT_SCHEMA = {")
    content = content.replace("SUMMARY_SCHEMA = {", "# SUMMARY_SCHEMA = {")

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)
    print("🎉 Gemini call successfully deleted and replaced with clean static compiler!")

if __name__ == "__main__":
    main()
