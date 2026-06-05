import json
import os
import sys

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
                
            analysis = p.get("analysis", {})
            if not isinstance(analysis, dict):
                errors.append(f"products[{idx}].analysis must be an object")
            else:
                for key in ["pros", "cons", "recommended_for"]:
                    val = analysis.get(key)
                    if val is None or not isinstance(val, list):
                        errors.append(f"products[{idx}].analysis.{key} must be an array (null not allowed)")
                        
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
                    
    if errors:
        print("Validation FAILED with the following errors:")
        for err in errors:
            print(f"- {err}")
        sys.exit(1)
    else:
        print("validation passed")
        sys.exit(0)

if __name__ == "__main__":
    validate()
