import json
import os
import re
import sys

FORBIDDEN_WORDS = [
    "最強", "神", "圧倒的", "超おすすめ",
    "おすすめ", "ぴったり", "最適", "心強い", "頼もしい",
    "納得", "魅力", "味方", "パートナー", "相棒",
]

COLLOQUIAL_PATTERNS = ["だよ", "だね", "んだ"]

NO_INFO_PHRASES = ["該当情報なし"]


def find_repeated_substrings(text, min_len=8, min_count=3):
    counts = {}
    for i in range(len(text) - min_len + 1):
        sub = text[i:i + min_len]
        counts[sub] = counts.get(sub, 0) + 1
    return [s for s, c in counts.items() if c >= min_count]


def validate():
    draft_path = "article_draft.json"
    if not os.path.exists(draft_path):
        print(f"Error: {draft_path} not found.")
        sys.exit(1)
        
    try:
        with open(draft_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        print(f"Error parsing JSON: {e}")
        sys.exit(1)
        
    errors = []
    
    # 1. meta
    meta = data.get("meta", {})
    if not isinstance(meta, dict):
        errors.append("meta must be an object")
    else:
        title = meta.get("title")
        if not title or not isinstance(title, str) or not title.strip():
            errors.append("meta.title must exist and not be empty")
            
        excerpt = meta.get("excerpt", "")
        if not isinstance(excerpt, str):
            errors.append("meta.excerpt must be a string")
        else:
            excerpt_len = len(excerpt)
            if not (80 <= excerpt_len <= 150):
                errors.append(f"meta.excerpt must be 80-150 chars (current: {excerpt_len} chars)")
                
    # 2. content
    content = data.get("content", {})
    if not isinstance(content, dict):
        errors.append("content must be an object")
    else:
        intro = content.get("intro", "")
        if not isinstance(intro, str):
            errors.append("content.intro must be a string")
        else:
            intro_len = len(intro)
            if not (200 <= intro_len <= 400):
                errors.append(f"content.intro must be 200-400 chars (current: {intro_len} chars)")
                
        summary = content.get("summary", "")
        if not isinstance(summary, str):
            errors.append("content.summary must be a string")
        else:
            summary_len = len(summary)
            if not (200 <= summary_len <= 300):
                errors.append(f"content.summary must be 200-300 chars (current: {summary_len} chars)")
                
    # 3. products
    products = data.get("products", [])
    if not isinstance(products, list):
        errors.append("products must be an array")
    else:
        prod_count = len(products)
        if not (1 <= prod_count <= 6):
            errors.append(f"products must have 1-6 items (current: {prod_count})")
            
        names = []
        for idx, p in enumerate(products):
            if not isinstance(p, dict):
                errors.append(f"products[{idx}] must be an object")
                continue
            name = p.get("name")
            if not name or not isinstance(name, str) or not name.strip():
                errors.append(f"products[{idx}].name is missing or empty")
            else:
                names.append(name.strip())

            description = p.get("description", "")
            if isinstance(description, str) and len(description) > 400:
                errors.append(f"products[{idx}].description exceeds 400 chars (current: {len(description)} chars)")

            analysis = p.get("analysis", {})
            if not isinstance(analysis, dict):
                errors.append(f"products[{idx}].analysis must be an object")
            else:
                for key in ["pros", "cons", "recommended_for"]:
                    val = analysis.get(key)
                    if val is None or not isinstance(val, list):
                        errors.append(f"products[{idx}].analysis.{key} must be an array (null not allowed)")

                cons = analysis.get("cons")
                if isinstance(cons, list):
                    for c in cons:
                        if isinstance(c, str) and any(phrase in c for phrase in NO_INFO_PHRASES):
                            errors.append(f"products[{idx}].analysis.cons contains forbidden phrase '該当情報なし'")

        if len(names) != len(set(names)):
            errors.append("products name duplicate detected")
            
    # 4. ui
    ui = data.get("ui", {})
    if not isinstance(ui, dict):
        errors.append("ui must be an object")
    else:
        faq = ui.get("faq", [])
        if not isinstance(faq, list):
            errors.append("ui.faq must be an array")
        else:
            faq_count = len(faq)
            if not (1 <= faq_count <= 3):
                errors.append(f"ui.faq must have 1-3 items (current: {faq_count})")
            for idx, item in enumerate(faq):
                if not isinstance(item, dict):
                    errors.append(f"ui.faq[{idx}] must be an object")
                    continue
                q = item.get("question")
                a = item.get("answer")
                if not q or not isinstance(q, str) or not q.strip():
                    errors.append(f"ui.faq[{idx}].question is empty or missing")
                if not a or not isinstance(a, str) or not a.strip():
                    errors.append(f"ui.faq[{idx}].answer is empty or missing")
    # 5. Text corruption check
    json_str = json.dumps(data, ensure_ascii=False)
    if " of " in json_str:
        errors.append("日本語破損表現の ' of ' が検出されました")

    # 6. Collect all human-written text for word/phrase/structure checks
    text_fields = []
    if isinstance(meta, dict):
        text_fields.append(meta.get("title", "") or "")
        text_fields.append(meta.get("excerpt", "") or "")
    if isinstance(content, dict):
        text_fields.append(content.get("intro", "") or "")
        text_fields.append(content.get("summary", "") or "")
    if isinstance(products, list):
        for p in products:
            if not isinstance(p, dict):
                continue
            text_fields.append(p.get("description", "") or "")
            analysis = p.get("analysis", {})
            if isinstance(analysis, dict):
                for key in ["pros", "cons", "recommended_for"]:
                    val = analysis.get(key)
                    if isinstance(val, list):
                        text_fields.extend(v for v in val if isinstance(v, str))
    if isinstance(ui, dict):
        for point in ui.get("points", []) or []:
            if isinstance(point, str):
                text_fields.append(point)
        for item in ui.get("faq", []) or []:
            if isinstance(item, dict):
                text_fields.append(item.get("question", "") or "")
                text_fields.append(item.get("answer", "") or "")

    full_text = "".join(text_fields)

    # 7. Forbidden words
    for word in FORBIDDEN_WORDS:
        if word in full_text:
            errors.append(f"禁止語 '{word}' が検出されました")

    # 8. Colloquial endings
    for pattern in COLLOQUIAL_PATTERNS:
        if pattern in full_text:
            errors.append(f"口語表現 '{pattern}' が検出されました")

    # 9. Repeated substrings (8+ chars repeated 3+ times across the article)
    repeated = find_repeated_substrings(full_text, min_len=8, min_count=3)
    if repeated:
        sample = repeated[0]
        errors.append(f"8文字以上の文字列が3回以上重複しています（例: '{sample}'）")

    if errors:
        print("Validation FAILED with the following errors:")
        for err in errors:
            print(f"- {err}")
        return False
    else:
        print("validation passed")
        return True

if __name__ == "__main__":
    if validate():
        sys.exit(0)
    else:
        sys.exit(1)
