#!/usr/bin/env python3
"""
Notionの「みっけ！競合記事キュー」から未処理の競合URL（my-best.com等）を1件取得し、
スクレイピングして商品情報とアフィリエイトリンク・画像を自動収集してJSONに書き出すスクリプト。
"""

import os
import sys
import json
import requests
import urllib.parse
import re
import time
from dotenv import load_dotenv

# プロジェクトルートのパスを追加
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# .env.local をロード
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env.local"))

NOTION_API_KEY = os.getenv("NOTION_API_KEY")
DATABASE_ID = "36cddb45-8772-80c3-ab74-eb061ecee73f"  # 「みっけ！競合記事キュー」のID

if not NOTION_API_KEY:
    print("❌ エラー: NOTION_API_KEY が .env.local に設定されていません。")
    sys.exit(1)

NOTION_HEADERS = {
    "Authorization": f"Bearer {NOTION_API_KEY}",
    "Notion-Version": "2022-06-28",
    "Content-Type": "application/json"
}

def update_page_status(page_id: str, status_name: str):
    """Notionの特定ページのステータスプロパティを更新します。"""
    url = f"https://api.notion.com/v1/pages/{page_id}"
    payload = {
        "properties": {
            "Status": {
                "status": {"name": status_name}
            }
        }
    }
    try:
        requests.patch(url, headers=NOTION_HEADERS, json=payload, timeout=10)
    except Exception as e:
        print(f"⚠️ ステータス更新エラー: {e}")

def fetch_url_text_puppeteer(url: str) -> str:
    """Puppeteerを使ってヘッドレスブラウザでHTMLを動的に取得します。"""
    import subprocess
    import tempfile
    
    js_code = """
const puppeteer = require('puppeteer');
(async () => {
  const browser = await puppeteer.launch({
    headless: true,
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });
  const page = await browser.newPage();
  await page.setUserAgent('Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/120.0.0.0');
  try {
    await page.goto(process.argv[2], { waitUntil: 'networkidle2', timeout: 30000 });
    const html = await page.content();
    console.log(html);
  } catch (e) {
    console.error(e);
    process.exit(1);
  } finally {
    await browser.close();
  }
})();
"""
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    temp_js_path = os.path.join(project_root, "puppeteer_temp_scraper.js")
    
    try:
        with open(temp_js_path, "w", encoding="utf-8") as f:
            f.write(js_code)
            
        res = subprocess.run(
            ['node', temp_js_path, url],
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='ignore'
        )
        if res.returncode == 0:
            return res.stdout
        else:
            print(f"⚠️ Puppeteer実行エラー: {res.stderr}")
            return ""
    except Exception as e:
        print(f"⚠️ Puppeteer呼び出し失敗: {e}")
        return ""
    finally:
        if os.path.exists(temp_js_path):
            try:
                os.remove(temp_js_path)
            except Exception:
                pass

def extract_capacity(title: str) -> str:
    """容量（ml, gなど）を抽出します。タイトルマッチングの精度向上用。"""
    m = re.search(r'(\d+(?:ml|g|kg|L|枚|回分|本|個|oz))', title, re.IGNORECASE)
    return m.group(1).lower() if m else ""

def verify_title_match(target_title: str, candidate_title: str) -> bool:
    """2つの商品タイトルが一致しているか大雑把に検証します。"""
    if not target_title or not candidate_title:
        return True
    
    # 容量のチェック
    cap1 = extract_capacity(target_title)
    cap2 = extract_capacity(candidate_title)
    if cap1 and cap2 and cap1 != cap2:
        return False  # 容量が明示的に異なる場合は不一致
        
    # キーワードの一致度
    clean1 = re.sub(r'[\(\)（）\[\]【】\-\s]', '', target_title.lower())
    clean2 = re.sub(r'[\(\)（）\[\]【】\-\s]', '', candidate_title.lower())
    
    # 共通キーワードのチェック
    words = [w for w in re.split(r'[^a-zA-Z0-9\u3040-\u309f\u30a0-\u30ff\u4e00-\u9faf]', target_title) if len(w) >= 2]
    if not words:
        return True
        
    match_count = sum(1 for w in words if w.lower() in candidate_title.lower())
    match_rate = match_count / len(words)
    return match_rate >= 0.4

def fetch_product_details(query: str, jan_code: str = "", asin: str = ""):
    """Amazon, Yahoo, 楽天のAPIやスクレイピングから製品情報を取得します。"""
    details = {
        "image_url": "",
        "amazon_price": "なし",
        "rakuten_price": "なし",
        "yahoo_price": "なし",
        "rakuten_url": "",
        "yahoo_url": "",
        "amazon_url": "",
        "amazon_name": "なし",
        "rakuten_name": "なし",
        "yahoo_name": "なし"
    }
    
    browser_h = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/120.0.0.0"
    }

    # 1. Amazon
    clean_asin = asin.strip() if asin else ""
    if not clean_asin:
        search_queries = [jan_code.strip()] if jan_code else []
        search_queries.append(query)
        for q in search_queries:
            try:
                url = f"https://www.amazon.co.jp/s?k={urllib.parse.quote(q)}"
                res = requests.get(url, headers=browser_h, timeout=10)
                if res.status_code == 200:
                    match = re.search(r'data-asin="([A-Z0-9]{10})"[^>]*data-component-type="s-search-result"', res.text)
                    if not match:
                        match = re.search(r'data-component-type="s-search-result"[^>]*data-asin="([A-Z0-9]{10})"', res.text)
                    if match:
                        clean_asin = match.group(1)
                        break
            except Exception:
                continue

    amazon_product_name = ""
    if clean_asin:
        details["amazon_url"] = f"https://www.amazon.co.jp/dp/{clean_asin}?tag=mikkestyle-22"
        try:
            dp_url = f"https://www.amazon.co.jp/dp/{clean_asin}"
            res = requests.get(dp_url, headers=browser_h, timeout=10)
            if res.status_code == 200:
                title_match = re.search(r'<span id="productTitle"[^>]*>\s*(.*?)\s*</span>', res.text, re.DOTALL)
                if title_match:
                    amazon_product_name = re.sub(r'\s+', ' ', title_match.group(1)).strip()
                    details["amazon_name"] = amazon_product_name
                
                price_match = re.search(r'"priceMobileShowActionFraction":\s*"([^"]+)"|class="a-price-whole">([^<]+)<', res.text)
                if price_match:
                    price_val = price_match.group(1) or price_match.group(2)
                    details["amazon_price"] = re.sub(r'[^\d]', '', price_val) if price_val else "なし"
                
                img_match = re.search(r'"landingImage"\s*:\s*\{\s*"([^"]+)"|id="landingImage"[^>]*src="([^"]+)"', res.text)
                if img_match:
                    details["image_url"] = img_match.group(1) or img_match.group(2)
        except Exception:
            pass

    # 2. Yahoo Shopping
    yahoo_app_id = os.getenv("YAHOO_SHOPPING_APP_ID")
    if yahoo_app_id and jan_code:
        try:
            url = f"https://shopping.yahooapis.jp/ShoppingWebService/V3/itemSearch?appid={yahoo_app_id}&query={jan_code.strip()}&results=20"
            res = requests.get(url, timeout=10)
            if res.status_code == 200:
                hits = res.json().get("hits", [])
                for hit in hits:
                    hit_title = hit.get("name", "")
                    if verify_title_match(amazon_product_name or query, hit_title):
                        details["yahoo_price"] = str(hit.get("price", ""))
                        details["yahoo_url"] = hit.get("url", "")
                        details["yahoo_name"] = hit_title
                        if not details["image_url"]:
                            img_url = hit.get("image", {}).get("medium") or ""
                            if img_url and "/i/g/" in img_url:
                                img_url = img_url.replace("/i/g/", "/i/l/")
                            details["image_url"] = img_url
                        break
        except Exception:
            pass

    # 3. Rakuten
    rakuten_app_id = os.getenv("RAKUTEN_APP_ID")
    rakuten_access_key = os.getenv("RAKUTEN_ACCESS_KEY")
    rakuten_affiliate_id = os.getenv("RAKUTEN_AFFILIATE_ID")
    if rakuten_app_id and jan_code:
        try:
            endpoints = [
                ("https://app.rakuten.co.jp/services/api/IchibaItem/Search/20170426", {"applicationId": rakuten_app_id, "affiliateId": rakuten_affiliate_id, "keyword": jan_code.strip(), "format": "json", "hits": 20}),
                ("https://openapi.rakuten.co.jp/ichibams/api/IchibaItem/Search/20220601", {"applicationId": rakuten_app_id, "accessKey": rakuten_access_key, "affiliateId": rakuten_affiliate_id, "keyword": jan_code.strip(), "format": "json", "hits": 20})
            ]
            rak_headers = {
                "Referer": "https://www.mikke-style.com",
                "Origin": "https://www.mikke-style.com"
            }
            for endpoint_url, params in endpoints:
                if not params.get("applicationId"):
                    continue
                res = requests.get(endpoint_url, params=params, headers=rak_headers, timeout=10)
                if res.status_code == 200:
                    items = res.json().get("Items", [])
                    for item_wrapper in items:
                        item = item_wrapper.get("Item", {})
                        item_title = item.get("itemName", "")
                        if verify_title_match(amazon_product_name or query, item_title):
                            details["rakuten_price"] = str(item.get("itemPrice", ""))
                            details["rakuten_url"] = item.get("affiliateUrl") or item.get("itemUrl") or ""
                            details["rakuten_name"] = item_title
                            if not details["image_url"]:
                                img_url = item.get("mediumImageUrls", [{}])[0].get("imageUrl") or ""
                                if img_url:
                                    details["image_url"] = re.sub(r'\?_ex=\d+x\d+', '?_ex=640x640', img_url)
                            break
                    if details["rakuten_url"]:
                        break
        except Exception:
            pass

    if not details["image_url"]:
        details["image_url"] = "https://images.unsplash.com/photo-1527443224154-c4a3942d3acf?w=500"
    return details

def extract_mybest_ranking(html: str, url: str) -> list:
    """my-best.comのHTMLからJSON-LDを用いて正確に商品リストを抽出します。"""
    try:
        json_ld_blocks = re.findall(r'<script type="application/ld\+json">(.*?)</script>', html, re.DOTALL)
        for block in json_ld_blocks:
            try:
                data = json.loads(block.strip())
                if isinstance(data, dict) and data.get("@type") == "Article":
                    main_entity = data.get("mainEntity")
                    item_lists = []
                    if isinstance(main_entity, list):
                        item_lists = main_entity
                    elif isinstance(main_entity, dict):
                        item_lists = [main_entity]
                    
                    for item in item_lists:
                        if isinstance(item, dict) and item.get("@type") == "ItemList":
                            list_items = item.get("itemListElement", [])
                            if not list_items:
                                continue
                            
                            products = []
                            sorted_items = []
                            for li in list_items:
                                pos = li.get("position")
                                if pos is not None:
                                    try: pos = int(pos)
                                    except ValueError: pos = 999
                                else: pos = 999
                                sorted_items.append((pos, li))
                            sorted_items.sort(key=lambda x: x[0])
                            
                            for rank, li in sorted_items:
                                prod = li.get("item", {})
                                if not isinstance(prod, dict):
                                    continue
                                name = prod.get("name") or li.get("name") or ""
                                gtin = prod.get("gtin") or ""
                                asin = prod.get("asin") or ""
                                desc = prod.get("description") or prod.get("reviewBody") or ""
                                
                                products.append({
                                    "rank": rank,
                                    "name": name,
                                    "jan_code": gtin,
                                    "asin": asin,
                                    "description": desc
                                })
                            
                            if products:
                                return products
            except Exception:
                pass
    except Exception:
        pass
    
    # フォールバック: 見出し抽出
    products = []
    matches = re.findall(r'<h[234][^>]*>(?:第)?(\d+)位[:：\s]*([^<]+)</h[234]>', html, re.IGNORECASE)
    if not matches:
        matches = re.findall(r'>\s*(?:第)?(\d+)位[:：\s]*([^<]+)<', html)
    
    if matches:
        seen_ranks = set()
        for rank_str, name in matches:
            try: rank = int(rank_str)
            except ValueError: continue
            name = name.strip()
            if rank not in seen_ranks and name:
                seen_ranks.add(rank)
                products.append({
                    "rank": rank,
                    "name": name,
                    "jan_code": "",
                    "asin": "",
                    "description": ""
                })
        products.sort(key=lambda x: x["rank"])
        
    return products

def main():
    print("🔍 Notionからステータス「未処理」のキュー記事を探索中...")
    
    # クエリの作成
    payload = {
        "filter": {
            "property": "Status",
            "status": {"equals": "未処理"}
        },
        "sorts": [
            {
                "timestamp": "created_time",
                "direction": "ascending"
            }
        ],
        "page_size": 1
    }
    
    res = requests.post(f"https://api.notion.com/v1/databases/{DATABASE_ID}/query", headers=NOTION_HEADERS, json=payload)
    if res.status_code != 200:
        print(f"❌ Notionデータベースのクエリに失敗しました: {res.status_code} {res.text}")
        sys.exit(1)
        
    results = res.json().get("results", [])
    if not results:
        print("ℹ️ 「未処理」の競合記事URLはありません。処理を終了します。")
        sys.exit(0)
        
    page = results[0]
    page_id = page["id"]
    props = page["properties"]
    
    url_prop = props.get("URL") or {}
    competitor_url = url_prop.get("url") or ""
    
    cat_prop = props.get("Category") or {}
    category = "ガジェット"
    if cat_prop and isinstance(cat_prop, dict):
        select_val = cat_prop.get("select")
        if select_val:
            category = select_val.get("name", "ガジェット")
            
    title_prop = props.get("Name", {}).get("title") or []
    name_str = title_prop[0].get("plain_text") if title_prop else "Untitled"
    
    if not competitor_url:
        print(f"⚠️ 行「{name_str}」のURLが空です。ステータスをエラーに変更します。")
        update_page_status(page_id, "エラー")
        sys.exit(1)
        
    print(f"🚀 ターゲット発見！")
    print(f"  タイトル(仮): {name_str}")
    print(f"  競合URL: {competitor_url}")
    print(f"  カテゴリ: {category}")
    
    # ステータスを「処理中」に変更
    update_page_status(page_id, "処理中")
    
    print(f"⏳ 競合ページのHTMLをダウンロード中...")
    html = fetch_url_text_puppeteer(competitor_url)
    if not html:
        print("❌ HTMLの取得に失敗しました。")
        update_page_status(page_id, "エラー")
        sys.exit(1)
        
    print("📦 ランキングリストと商品データを抽出中...")
    products = extract_mybest_ranking(html, competitor_url)
    
    if not products:
        print("❌ 商品の抽出に失敗しました。mybest形式でないか、DOMが変更された可能性があります。")
        update_page_status(page_id, "エラー")
        sys.exit(1)
        
    print(f"🎉 成功！ {len(products)} 個の商品を検出しました。")
    
    # 最大6個に制限
    selected_products = products[:6]
    print(f"ℹ️ 上位 {len(selected_products)} 件の商品のアフィリエイト詳細情報を取得します...")
    
    final_products_list = []
    for idx, p in enumerate(selected_products):
        print(f"[{idx+1}/{len(selected_products)}] {p['name']} の情報を検索中...")
        details = fetch_product_details(p["name"], p["jan_code"], p["asin"])
        
        final_products_list.append({
            "rank": p["rank"],
            "original_name": p["name"],
            "jan_code": p["jan_code"],
            "asin": p["asin"],
            "competitor_description": p["description"],
            "resolved_details": details
        })
        time.sleep(1)
        
    # 出力データの準備
    output_data = {
        "page_id": page_id,
        "competitor_url": competitor_url,
        "default_category": category,
        "default_title": name_str,
        "products": final_products_list
    }
    
    output_filepath = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scripts", "stockpile_data.json")
    with open(output_filepath, "w", encoding="utf-8") as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)
        
    print("=" * 60)
    print("🔥 データの収集が完了しました！")
    print(f"💾 データファイル保存場所: {output_filepath}")
    print("=" * 60)
    
    # 画面に情報を美しくダンプする
    print("\n【🌟 記事執筆用 抽出商品サマリー】")
    for p in final_products_list:
        d = p["resolved_details"]
        print(f"\n🌸 第{p['rank']}位: {p['original_name']}")
        if p['jan_code']: print(f"   - JANコード: {p['jan_code']}")
        if p['asin']: print(f"   - ASIN: {p['asin']}")
        print(f"   - Amazon名: {d['amazon_name']} (価格: {d['amazon_price']}円)")
        print(f"   - 楽天名: {d['rakuten_name']} (価格: {d['rakuten_price']}円)")
        print(f"   - Yahoo名: {d['yahoo_name']} (価格: {d['yahoo_price']}円)")
        print(f"   - アフィリエイトURL:")
        if d['amazon_url']: print(f"     * Amazon: {d['amazon_url']}")
        if d['rakuten_url']: print(f"     * 楽天: {d['rakuten_url']}")
        if d['yahoo_url']: print(f"     * Yahoo: {d['yahoo_url']}")
        print(f"   - 画像URL: {d['image_url'][:80]}...")
        
    print("\n✅ ステータスは「処理中」にしてあります。")
    print("   これからAntigravity（AI）が本データを元に執筆を行い、ファイルを保存・本番公開します。")

if __name__ == "__main__":
    main()
