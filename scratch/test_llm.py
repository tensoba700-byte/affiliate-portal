import json
import os
import google.generativeai as genai
from dotenv import load_dotenv

# Load env from local directory
load_dotenv(".env.local")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

ARTICLE_SCHEMA = {
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
}

def main():
    with open("scripts/stockpile_data.json", "r", encoding="utf-8") as f:
        stockpile_data = json.load(f)
        
    products_input = []
    for p in stockpile_data.get("products", [])[:6]:
        products_input.append({
            "name": p.get("original_name", ""),
            "competitor_description": p.get("competitor_description", "")
        })

    prompt = f"""あなたはプロのWebライターとして、中立的かつ信頼性の高い商品紹介記事を執筆してください。
読者に親しみやすさを感じさせつつも、過度な装飾やAI特有の極端な表現を避けた、誠実なトーンを維持してください。

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
4. **商品説明の制限**: 各商品の紹介（description）は、**必ず1000文字以上**で詳細に記述してください。競合の商品説明（competitor_description）の具体的な特徴やメリットをベースにし、コピペではなく、独自の表現で1000文字以上のリッチなコンテンツに書き直してください。（出力上限内に収めるため、1000〜1200文字程度を目安とし、1500文字を超えないよう調整してください）
5. **絵文字の活用**: 各見出しおよび商品説明において、絵文字は**1商品につき1〜2個まで**に制限してください。さらに、商品の仕様（フルスペクトル、クリップ、調光など）に完全に適合した実用アイコンのみを使用し、抽象的な無関係な絵文字は含めないでください。
6. **ターゲット層**: 各商品に対し、「こんな人におすすめ！」という項目で、具体的な推奨理由を**3つの箇条書き**で作成してください。
7. **変数名禁止**: YAHOO_PRICE・RAKUTEN_PRICE・AMAZON_PRICE・YAHOOなどの変数名を文中に絶対に含めないでください。
8. **段落分け**: 各段落は**1〜2文程度**とし、段落間には空行（\\n\\n）を入れてスマホで最も読みやすい構成にしてください。また、文章が長く繋がらないように配慮してください。
9. **記事タイトル自動生成**:
   - 競合記事タイトルを参考に、GENERATION_RULESに定められた【情緒 × 機能の二段構え】の美しいタイトルを自動生成してください。
   - 禁止ワード（「おすすめ〇選」「人気〇選」「ランキング」「比較」「2024」「2026」など）は絶対に使用しないでください。
   - タイトルは次の形式にしてください: `[情緒的なメインタイトル]。【[機能的なサブタイトル]6選】` (必ず full-width period `。` を入れ、最後は `6選】` で終わるようにしてください)

出力形式: JSONスキーマに完全に従ってください。"""

    print("Sending request to Gemini...")
    model = genai.GenerativeModel('models/gemini-2.5-flash')
    res = model.generate_content(
        prompt,
        generation_config=genai.types.GenerationConfig(
            temperature=0.3,
            max_output_tokens=8192,
            response_mime_type="application/json",
            response_schema=ARTICLE_SCHEMA
        )
    )
    
    text = res.text
    print(f"Response received. Length: {len(text)}")
    try:
        data = json.loads(text)
        print("✅ Successfully parsed JSON!")
        print("Title:", data.get("title"))
        for i, p in enumerate(data.get("products")):
            print(f"Product {i+1} name: {p.get('name')} | Desc length: {len(p.get('description'))}")
    except Exception as e:
        print("❌ JSON parse failed:", e)
        print("Raw text tail (1000 chars):")
        print(text[-1000:])
        with open("raw_response.json", "w", encoding="utf-8") as f:
            f.write(text)
        print("Saved raw response to raw_response.json")

if __name__ == "__main__":
    main()
