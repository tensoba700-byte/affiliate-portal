import json
import os
import sys
import re

def validate():
    draft_path = "column_draft.json"
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
    warnings = []
    
    # JSON全体の文字列を取得して一括チェック
    json_str = json.dumps(data, ensure_ascii=False)
    
    # 1. 日本語破損表現・不自然な日本語の検出
    if " of " in json_str:
        errors.append("日本語破損表現である ' of ' が検出されました。")
        
    unnatural_nda_matches = re.findall(r"[一-龠ァ-ヶa-zA-Z0-9々ヶ]んだ", json_str)
    if unnatural_nda_matches:
        errors.append(f"不自然な日本語表現（名詞などの直後に直接 'んだ' が接続）が検出されました: {unnatural_nda_matches}")
        
    # 2. アフィリエイト関連リンク・プレースホルダーの検出
    affiliate_patterns = [
        r"amazon\.co\.jp",
        r"rakuten\.co\.jp",
        r"shopping\.yahoo\.co\.jp",
        r"valuecommerce\.com",
        r"hb\.afl\.rakuten\.co\.jp",
        r"ck\.jp\.ap\.valuecommerce\.com",
        r"\[AMAZON_LINK_HERE\]",
        r"\[RAKUTEN_LINK_HERE\]",
        r"\[YAHOO_LINK_HERE\]"
    ]
    for pattern in affiliate_patterns:
        if re.search(pattern, json_str, re.IGNORECASE):
            errors.append(f"禁止されているアフィリエイトリンクまたはプレースホルダーが検出されました: {pattern}")
            
    # 3. 比較記事的表現の警告（Warning）
    warning_patterns = [
        (r"第[0-9１２３４５６７８９〇一二三四五六七八九十]位", "順位・第◯位"),
        (r"ランキング", "ランキング"),
        (r"徹底比較", "徹底比較"),
        (r"売れ筋", "売れ筋"),
        (r"ベストコスメ", "ベストコスメ"),
        (r"ベスコス", "ベスコス")
    ]
    for pattern, name in warning_patterns:
        matches = re.findall(pattern, json_str)
        if matches:
            warnings.append(f"比較記事的表現 '{name}' が検出されました (検出数: {len(matches)}回)")

    # 4. スキーマ検証
    # meta
    meta = data.get("meta", {})
    if not isinstance(meta, dict):
        errors.append("meta must be an object")
    else:
        for key in ["slug", "title", "category", "publish_date", "description"]:
            val = meta.get(key)
            if not val or not isinstance(val, str) or not val.strip():
                errors.append(f"meta.{key} must exist and not be empty")
        
        # descriptionの文字数チェック (80〜150字)
        desc = meta.get("description", "")
        if isinstance(desc, str) and desc.strip():
            desc_len = len(desc)
            if not (80 <= desc_len <= 150):
                errors.append(f"meta.description must be 80-150 chars (current: {desc_len} chars)")

    # content
    content = data.get("content", {})
    if not isinstance(content, dict):
        errors.append("content must be an object")
    else:
        # lead (200〜400字)
        lead = content.get("lead", "")
        if not lead or not isinstance(lead, str) or not lead.strip():
            errors.append("content.lead must exist and not be empty")
        else:
            lead_len = len(lead)
            if not (200 <= lead_len <= 400):
                errors.append(f"content.lead must be 200-400 chars (current: {lead_len} chars)")

        # summary (200〜300字)
        summary = content.get("summary", "")
        if not summary or not isinstance(summary, str) or not summary.strip():
            errors.append("content.summary must exist and not be empty")
        else:
            summary_len = len(summary)
            if not (200 <= summary_len <= 300):
                errors.append(f"content.summary must be 200-300 chars (current: {summary_len} chars)")

        # sections
        sections = content.get("sections", [])
        if not isinstance(sections, list) or not sections:
            errors.append("content.sections must be a non-empty array")
        else:
            if not (1 <= len(sections) <= 8):
                errors.append(f"content.sections must have 1-8 sections (current: {len(sections)})")
            for idx, sec in enumerate(sections):
                if not isinstance(sec, dict):
                    errors.append(f"content.sections[{idx}] must be an object")
                    continue
                heading = sec.get("heading")
                body = sec.get("body")
                point = sec.get("point")
                if not heading or not isinstance(heading, str) or not heading.strip():
                    errors.append(f"content.sections[{idx}].heading must exist and not be empty")
                if not body or not isinstance(body, str) or not body.strip():
                    errors.append(f"content.sections[{idx}].body must exist and not be empty")
                if point is not None:
                    if not isinstance(point, str) or not point.strip():
                        errors.append(f"content.sections[{idx}].point must be a non-empty string if present")

        # faq (任意)
        faq = content.get("faq")
        if faq is not None:
            if not isinstance(faq, list):
                errors.append("content.faq must be an array")
            else:
                for idx, item in enumerate(faq):
                    if not isinstance(item, dict):
                        errors.append(f"content.faq[{idx}] must be an object")
                        continue
                    q = item.get("question")
                    a = item.get("answer")
                    if not q or not isinstance(q, str) or not q.strip():
                        errors.append(f"content.faq[{idx}].question must exist and not be empty")
                    if not a or not isinstance(a, str) or not a.strip():
                        errors.append(f"content.faq[{idx}].answer must exist and not be empty")

    # related_articles (任意)
    related_articles = data.get("related_articles")
    if related_articles is not None:
        if not isinstance(related_articles, list):
            errors.append("related_articles must be an array")
        else:
            for idx, slug in enumerate(related_articles):
                if not isinstance(slug, str) or not slug.strip():
                    errors.append(f"related_articles[{idx}] must be a non-empty string")

    # 結果出力
    if warnings:
        print("Validation WARNINGS:")
        for warn in warnings:
            print(f"⚠️ {warn}")
            
    if errors:
        print("\nValidation FAILED with the following errors:")
        for err in errors:
            print(f"❌ - {err}")
        return False
    else:
        print("\nValidation PASSED successfully")
        return True

if __name__ == "__main__":
    if validate():
        sys.exit(0)
    else:
        sys.exit(1)
