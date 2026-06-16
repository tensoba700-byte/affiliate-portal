import os
import requests
import re
import unicodedata
from dotenv import load_dotenv

load_dotenv(".env.local")

app_id = os.getenv("RAKUTEN_APP_ID")
access_key = os.getenv("RAKUTEN_ACCESS_KEY")
affiliate_id = os.getenv("RAKUTEN_AFFILIATE_ID")
rak_headers = {
    "Referer": "https://www.mikke-style.com",
    "Origin": "https://www.mikke-style.com"
}

def generate_search_keywords(name: str) -> list:
    s = name.replace("BEYONDNILE", "BEYOND NILE")
    s = s.replace("YOUNGBIOHEAL", "YOUNG BIOHEAL")
    s = re.sub(r'[\uff5c\uff0f|/：:;；,，.．_＿\-─\(\)（）]', ' ', s)
    s = re.sub(r'([a-z])([A-Z])', r'\1 \2', s)
    s = re.sub(r'([a-zA-Z0-9]+)([\u3040-\u309f\u30a0-\u30ff\u4e00-\u9faf]+)', r'\1 \2', s)
    s = re.sub(r'([\u3040-\u309f\u30a0-\u30ff\u4e00-\u9faf]+)([a-zA-Z0-9]+)', r'\1 \2', s)
    
    words = [w.strip() for w in s.split() if w.strip()]
    if not words:
        return [name]
        
    keywords = []
    stop_words = {"the", "founders", "brand", "official", "co", "ltd", "inc", "japan", "公式", "ブランド", "日本", "aiロボティクス", "ai", "beyond", "cj", "olive", "young"}
    filtered_words = [w for w in words if w.lower() not in stop_words]
    
    eng_words = [w for w in filtered_words if re.match(r'^[a-zA-Z0-9]+$', w) and len(w) >= 2]
    jp_words = [w for w in filtered_words if not re.match(r'^[a-zA-Z0-9]+$', w) and len(w) >= 2]
    
    if eng_words and jp_words:
        keywords.append(f"{eng_words[0]} {jp_words[0]}")
        if len(jp_words) > 1:
            keywords.append(f"{eng_words[0]} {jp_words[1]}")
            
    if filtered_words:
        clean_filtered = [w for w in filtered_words if len(w) >= 2]
        if clean_filtered:
            keywords.append(" ".join(clean_filtered[:3]))
            if len(clean_filtered) >= 2:
                keywords.append(" ".join(clean_filtered[:2]))
            
    keywords.append(" ".join(words[:4]))
    if len(words) >= 2:
        keywords.append(" ".join(words[:2]))
    if len(words) >= 3:
        keywords.append(" ".join(words[:3]))
            
    seen = set()
    unique_keywords = []
    for kw in keywords:
        kw_clean = " ".join(kw.split())
        parts = kw_clean.split()
        if all(len(p) >= 2 for p in parts):
            if kw_clean and kw_clean not in seen:
                seen.add(kw_clean)
                unique_keywords.append(kw_clean)
    return unique_keywords

def extract_capacity(title: str) -> str:
    normalized_title = unicodedata.normalize('NFKC', title)
    m = re.search(r'(\d+(?:ml|g|kg|L|枚|回分|本|個|oz))', normalized_title, re.IGNORECASE)
    return m.group(1).lower() if m else ""

def verify_title_match(target_title: str, candidate_title: str) -> bool:
    if not target_title or not candidate_title:
        return True
    
    target_norm = unicodedata.normalize('NFKC', target_title)
    candidate_norm = unicodedata.normalize('NFKC', candidate_title)
    
    cap1 = extract_capacity(target_norm)
    cap2 = extract_capacity(candidate_norm)
    if cap1 and cap2 and cap1 != cap2:
        return False
        
    words = [w for w in re.split(r'[^a-zA-Z0-9\u3040-\u309f\u30a0-\u30ff\u4e00-\u9faf]', target_norm) if len(w) >= 2]
    
    clean_candidate = re.sub(r'[\s\u3000]', '', candidate_norm.lower())
    match_count = sum(1 for w in words if re.sub(r'[\s\u3000]', '', w.lower()) in clean_candidate)
    if not words:
        return True
    match_rate = match_count / len(words)
    return match_rate >= 0.3

def test_keywords(query):
    kws = generate_search_keywords(query)
    print(f"Keywords generated: {kws}")
    
    url = "https://openapi.rakuten.co.jp/ichibams/api/IchibaItem/Search/20220601"
    for kw in kws:
        params = {
            "format": "json",
            "applicationId": app_id,
            "accessKey": access_key,
            "affiliateId": affiliate_id,
            "keyword": kw,
            "imageFlag": 1,
            "hits": 5
        }
        print(f"--- Searching Keyword: '{kw}' ---")
        try:
            res = requests.get(url, params=params, headers=rak_headers, timeout=10)
            if res.status_code == 200:
                items = res.json().get("Items", [])
                print(f"Found {len(items)} items.")
                for i, item_wrapper in enumerate(items):
                    item = item_wrapper.get("Item", {})
                    title = item.get("itemName", "")
                    matched = verify_title_match(query, title)
                    print(f"  [{i+1}] Match: {matched} | {title[:60]}...")
            else:
                print(f"  Error {res.status_code}: {res.text}")
        except Exception as e:
            print(f"  Error: {e}")

test_keywords("CJ OLIVE YOUNGBIOHEAL BOH ｜ プロバイオダーム 3Dリフティングクリームマスク")
