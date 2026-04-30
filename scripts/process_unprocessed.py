#!/usr/bin/env python3
"""みっけ！記事管理の「未処理」商品を処理するスクリプト（商品選定スコアリング付き）"""
import html as html_lib
import json
import os
import requests
import urllib.parse
import re
import time
from pathlib import Path


def _load_env():
    """プロジェクトルートの .env.local を os.environ に読み込む"""
    env_path = Path(__file__).parent.parent / ".env.local"
    if not env_path.exists():
        return
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, val = line.partition("=")
        os.environ.setdefault(key.strip(), val.strip())

_load_env()


def _require(key: str) -> str:
    val = os.environ.get(key, "")
    if not val or val.startswith("your_"):
        raise RuntimeError(f"環境変数 {key} が未設定です（.env.local を確認してください）")
    return val


NOTION_API_KEY     = _require("NOTION_API_KEY")
DATABASE_ID        = _require("NOTION_DATABASE_ID")
RAKUTEN_APP_ID     = _require("RAKUTEN_APP_ID")
RAKUTEN_ACCESS_KEY = _require("RAKUTEN_ACCESS_KEY")
RAKUTEN_AFFILIATE_ID = _require("RAKUTEN_AFFILIATE_ID")
AMAZON_TAG         = _require("AMAZON_TAG")
_yahoo_sid         = _require("YAHOO_AFFILIATE_SID")
_yahoo_pid         = _require("YAHOO_AFFILIATE_PID")
YAHOO_AFFILIATE_BASE = (
    f"https://ck.jp.ap.valuecommerce.com/servlet/referral"
    f"?sid={_yahoo_sid}&pid={_yahoo_pid}&vc_url="
)

NOTION_H = {
    "Authorization": f"Bearer {NOTION_API_KEY}",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28"
}
BROWSER_H = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept-Language": "ja,en;q=0.9"
}
RAKUTEN_H = {
    "Referer": "https://www.mikke-style.com",
    "Origin": "https://www.mikke-style.com"
}


# ── ユーティリティ ────────────────────────────────────
def score_match(product_name: str, candidate_title: str) -> int:
    tokens = re.findall(r'[a-z0-9]+|[぀-ヿ一-鿿]{2,}', product_name.lower())
    if not tokens:
        return 0
    matched = sum(1 for t in tokens if t in candidate_title.lower())
    return matched * 100 // len(tokens)


def shorten_query(query: str) -> str:
    tokens = query.split()
    trimmed = [t for t in tokens if not re.fullmatch(r'[A-Z0-9][-A-Z0-9]{3,}', t)]
    return " ".join(trimmed[:6]) if trimmed else query


def get_text(prop) -> str:
    if not prop:
        return ""
    arr = prop.get("rich_text", []) or prop.get("title", [])
    return arr[0].get("plain_text", "") if arr else ""


def get_url(prop) -> str:
    return (prop or {}).get("url") or ""


# ── 楽天検索（②リトライロジック追加・①閾値60%）────────
def extract_real_url(affiliate_url: str) -> str:
    m = re.search(r'[?&]pc=([^&]+)', affiliate_url)
    return urllib.parse.unquote(m.group(1)) if m else affiliate_url


def _rakuten_search_one(product_name: str, query: str):
    """1クエリ分の楽天検索。在庫あり→なしの順で試し、スコア最良を返す"""
    for avail in [1, 0]:
        try:
            res = requests.get(
                "https://openapi.rakuten.co.jp/ichibams/api/IchibaItem/Search/20220601",
                params={
                    "format": "json", "keyword": query,
                    "applicationId": RAKUTEN_APP_ID, "accessKey": RAKUTEN_ACCESS_KEY,
                    "affiliateId": RAKUTEN_AFFILIATE_ID,
                    "hits": 10, "sort": "standard", "availability": avail
                },
                headers=RAKUTEN_H, timeout=10
            ).json()
        except Exception as e:
            print(f"  楽天APIエラー: {e}")
            return None, -1

        if "errors" in res:
            print(f"  楽天APIエラー: {res['errors']}")
            return None, -1

        items = res.get("Items", [])
        if not items:
            continue

        best, best_score = None, -1
        for entry in items:
            item = entry["Item"]
            s = score_match(product_name, item.get("itemName", ""))
            if s > best_score:
                best_score, best = s, item

        if best:
            return best, best_score

    return None, -1


def search_rakuten(product_name: str, query: str):
    """楽天検索。60%未満なら最大3段階キーワードリトライ（②）"""
    queries = [query, shorten_query(query), product_name]
    seen, deduped = set(), []
    for q in queries:
        if q and q not in seen:
            seen.add(q)
            deduped.append(q)

    for attempt, q in enumerate(deduped, 1):
        print(f"  楽天検索中... (試行{attempt}: {q[:50]})")
        item, score = _rakuten_search_one(product_name, q)
        if item and score >= 60:  # ① 閾値 60%
            aff_url = item.get("affiliateUrl") or item.get("itemUrl", "")
            real_url = extract_real_url(aff_url)
            imgs = item.get("mediumImageUrls", [])
            img = imgs[0].get("imageUrl", "").replace("128x128", "500x500") if imgs else ""
            print(f"  → 採用: {score}% 「{item['itemName'][:40]}」")
            return {
                "ref_url": real_url,
                "affiliate_url": aff_url,
                "image": img,
                "price": str(item.get("itemPrice", ""))
            }
        if item:
            print(f"  → {score}%（60%未満）次のキーワードで再試行")
        time.sleep(1)

    print("  → 楽天: 60%以上の商品が見つかりませんでした")
    return None


# ── Amazon検索（③画像も取得）─────────────────────────
def get_asin_info(asin: str) -> tuple:
    """Amazon商品ページからタイトルと画像URLを取得（③）"""
    try:
        res = requests.get(f"https://www.amazon.co.jp/dp/{asin}", headers=BROWSER_H, timeout=10)
        text = res.text

        title = ""
        m = re.search(r'<span id="productTitle"[^>]*>(.*?)</span>', text, re.DOTALL)
        if m:
            title = re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', '', m.group(1))).strip()

        image = ""
        # data-old-hires が最高解像度
        m = re.search(r'data-old-hires="([^"]+)"', text)
        if m:
            image = m.group(1)
        else:
            # data-a-dynamic-image（JSON）から最大サイズURLを取得
            m = re.search(r'data-a-dynamic-image="([^"]+)"', text)
            if m:
                try:
                    imgs = json.loads(html_lib.unescape(m.group(1)))
                    if imgs:
                        image = max(imgs.items(), key=lambda x: x[1][0] * x[1][1])[0]
                except Exception:
                    pass

        return title, image
    except Exception:
        pass
    return "", ""


def _amazon_search_one(product_name: str, query: str):
    """1クエリ分のAmazon検索。上位5件をスコアリングして最良を返す"""
    try:
        res = requests.get(
            f"https://www.amazon.co.jp/s?k={urllib.parse.quote(query)}&l=ja_JP",
            headers=BROWSER_H, timeout=15
        )
        asins = list(dict.fromkeys(re.findall(r'/dp/([A-Z0-9]{10})', res.text)))[:5]
    except Exception as e:
        print(f"  Amazon検索エラー: {e}")
        return None, -1, "", ""

    best_asin, best_score, best_title, best_image = None, -1, "", ""
    for asin in asins:
        title, image = get_asin_info(asin)
        s = score_match(product_name, title) if title else 0
        print(f"    {asin} {s}% 「{title[:40]}」")
        if s > best_score:
            best_score, best_asin, best_title, best_image = s, asin, title, image
        time.sleep(0.5)
    return best_asin, best_score, best_title, best_image


def search_amazon(product_name: str, query: str):
    """Amazon検索。60%未満なら最大3段階キーワードリトライ"""
    queries = [query, shorten_query(query), product_name]
    seen, deduped = set(), []
    for q in queries:
        if q and q not in seen:
            seen.add(q)
            deduped.append(q)

    for attempt, q in enumerate(deduped, 1):
        print(f"  Amazon検索中... (試行{attempt}: {q[:50]})")
        asin, score, title, image = _amazon_search_one(product_name, q)
        if asin and score >= 60:
            print(f"  → 採用: {asin} {score}% 「{title[:40]}」")
            return {"url": f"https://www.amazon.co.jp/dp/{asin}", "asin": asin,
                    "score": score, "image": image}
        if asin:
            print(f"  → {score}%（60%未満）次のキーワードで再試行")
        time.sleep(1)

    print("  → Amazon: 60%以上の商品が見つかりませんでした")
    return None


# ── Yahoo検索（⑤URL抽出パターン追加）────────────────
def get_yahoo_title(url: str) -> str:
    try:
        res = requests.get(url, headers=BROWSER_H, timeout=10)
        m = re.search(r'<title[^>]*>(.*?)</title>', res.text, re.DOTALL)
        if m:
            title = re.sub(r'<[^>]+>', '', m.group(1)).strip()
            title = re.split(r'\s*[-|–]\s*Yahoo', title)[0].strip()
            return re.sub(r'\s+', ' ', title)
    except Exception:
        pass
    return ""


def _yahoo_search_one(product_name: str, query: str):
    try:
        res = requests.get(
            f"https://shopping.yahoo.co.jp/search?p={urllib.parse.quote(query)}&n=5",
            headers=BROWSER_H, timeout=15
        )
        html = res.text
        # ⑤ store.shopping.yahoo.co.jp と shopping.yahoo.co.jp/product/ の両パターン
        raw = (re.findall(r'https://store\.shopping\.yahoo\.co\.jp/[^\s"\'<>&]+', html) +
               re.findall(r'https://shopping\.yahoo\.co\.jp/product/[^\s"\'<>&]+', html))
        seen, urls = set(), []
        for u in raw:
            u = re.split(r'[?#]', u)[0].rstrip('/')
            if u not in seen:
                seen.add(u)
                urls.append(u)
        urls = urls[:5]
    except Exception as e:
        print(f"  Yahoo検索エラー: {e}")
        return None, -1, ""

    best_url, best_score, best_title = None, -1, ""
    for url in urls:
        title = get_yahoo_title(url)
        s = score_match(product_name, title) if title else 0
        print(f"    {url[:55]} {s}% 「{title[:30]}」")
        if s > best_score:
            best_score, best_url, best_title = s, url, title
        time.sleep(0.5)
    return best_url, best_score, best_title


def search_yahoo(product_name: str, query: str):
    """Yahoo検索。60%未満なら最大3段階キーワードリトライ"""
    queries = [query, shorten_query(query), product_name]
    seen, deduped = set(), []
    for q in queries:
        if q and q not in seen:
            seen.add(q)
            deduped.append(q)

    for attempt, q in enumerate(deduped, 1):
        print(f"  Yahoo検索中... (試行{attempt}: {q[:50]})")
        url, score, title = _yahoo_search_one(product_name, q)
        if url and score >= 60:
            affiliate = YAHOO_AFFILIATE_BASE + urllib.parse.quote(url, safe='')
            print(f"  → 採用: {score}% 「{title[:40]}」")
            return {"url": url, "affiliate_url": affiliate}
        if url:
            print(f"  → {score}%（60%未満）次のキーワードで再試行")
        time.sleep(1)

    print("  → Yahoo: 60%以上の商品が見つかりませんでした")
    return None


# ── Notion更新 ───────────────────────────────────────
def save_urls(page_id: str, data: dict) -> bool:
    """取得したURLやデータをNotionに保存する（ステータスは変更しない）"""
    props = {}

    if data.get("amazon_ref_url"):
        base = re.split(r'\?', data["amazon_ref_url"])[0]
        props["Amazon参考URL"] = {"url": base}
        props["Amazon Affiliate URL"] = {"url": f"{base}?tag={AMAZON_TAG}"}
        asin = data.get("amazon_asin", "")
        score = data.get("amazon_score", 0)
        if asin:
            props["ASIN"] = {"rich_text": [{"text": {"content": f"{asin} ({score}%)"}}]}

    if data.get("rakuten_ref_url"):
        props["楽天参考URL"] = {"url": data["rakuten_ref_url"]}
        props["Rakuten Affiliate URL"] = {"url": data["rakuten_affiliate_url"]}

    if data.get("yahoo_ref_url"):
        props["Yahoo参考URL"] = {"url": data["yahoo_ref_url"]}
        props["Yahoo Affiliate URL"] = {"url": data["yahoo_affiliate_url"]}

    if data.get("image_url"):
        props["Image URL"] = {"rich_text": [{"text": {"content": data["image_url"]}}]}
    if data.get("rakuten_price"):
        props["Rakuten Price"] = {"rich_text": [{"text": {"content": data["rakuten_price"]}}]}

    if not props:
        return False

    res = requests.patch(
        f"https://api.notion.com/v1/pages/{page_id}",
        headers=NOTION_H, json={"properties": props}
    )
    return res.status_code == 200


def mark_complete(page_id: str) -> bool:
    """ステータスを「完了」に更新する"""
    res = requests.patch(
        f"https://api.notion.com/v1/pages/{page_id}",
        headers=NOTION_H,
        json={"properties": {"ステータス 1": {"select": {"name": "完了"}}}}
    )
    return res.status_code == 200


def is_fully_fetched(data: dict, existing_props: dict) -> bool:
    """Amazon・楽天・Yahoo参考URL・Image URLが全て揃っているか確認（新規取得＋既存Notion両方を考慮）"""
    amazon_ok  = data.get("amazon_ref_url")  or get_url(existing_props.get("Amazon参考URL"))
    rakuten_ok = data.get("rakuten_ref_url") or get_url(existing_props.get("楽天参考URL"))
    yahoo_ok   = data.get("yahoo_ref_url")   or get_url(existing_props.get("Yahoo参考URL"))
    image_ok   = data.get("image_url")       or get_text(existing_props.get("Image URL"))
    return bool(amazon_ok and rakuten_ok and yahoo_ok and image_ok)


def get_unprocessed_items():
    # Notion APIはfilterのネストが2階層まで。
    # 「未処理」または「URLが空」のいずれかに該当するページを取得する。
    res = requests.post(
        f"https://api.notion.com/v1/databases/{DATABASE_ID}/query",
        headers=NOTION_H,
        json={
            "filter": {
                "or": [
                    {"property": "ステータス 1",       "select": {"equals": "未処理"}},
                    {"property": "Rakuten Affiliate URL", "url": {"is_empty": True}},
                    {"property": "Yahoo Affiliate URL",   "url": {"is_empty": True}},
                ]
            },
            "page_size": 100
        }
    )
    return res.json().get("results", [])


def main():
    items = get_unprocessed_items()
    print(f"対象件数: {len(items)}件\n")

    # ── Step 1: 全商品のURL取得・保存（ステータス変更なし）──
    # page_id -> (新規取得データ, 元のprops)
    item_results: dict[str, tuple[dict, dict]] = {}

    for i, page in enumerate(items):
        props = page["properties"]
        page_id = page["id"]
        product_name = get_text(props.get("商品名"))
        search_name  = get_text(props.get("検索商品名")) or product_name

        if not product_name:
            item_results[page_id] = ({}, props)
            continue

        has_amazon  = bool(get_url(props.get("Amazon Affiliate URL")))
        has_rakuten = bool(get_url(props.get("Rakuten Affiliate URL")))
        has_yahoo   = bool(get_url(props.get("Yahoo Affiliate URL")))

        print(f"[{i+1}/{len(items)}] {product_name}")
        print(f"  検索ワード: {search_name}")

        result = {}

        if not has_rakuten:
            rakuten = search_rakuten(product_name, search_name)
            if rakuten:
                result["rakuten_ref_url"]       = rakuten["ref_url"]
                result["rakuten_affiliate_url"] = rakuten["affiliate_url"]
                result["image_url"]             = rakuten["image"]
                result["rakuten_price"]         = rakuten["price"]
                print(f"  楽天参考URL: {rakuten['ref_url']}")
                print(f"  楽天価格: ¥{rakuten['price']}")
        else:
            print("  楽天: 取得済みスキップ")

        if not has_amazon:
            amazon = search_amazon(product_name, search_name)
            if amazon:
                result["amazon_ref_url"] = amazon["url"]
                result["amazon_asin"]    = amazon["asin"]
                result["amazon_score"]   = amazon["score"]
                print(f"  Amazon参考URL: {amazon['url']}")
                if not result.get("image_url") and amazon.get("image"):
                    result["image_url"] = amazon["image"]
                    print(f"  Image URL（Amazon代替）: {amazon['image'][:60]}...")
        else:
            print("  Amazon: 取得済みスキップ")

        if not has_yahoo:
            yahoo = search_yahoo(product_name, search_name)
            if yahoo:
                result["yahoo_ref_url"]       = yahoo["url"]
                result["yahoo_affiliate_url"] = yahoo["affiliate_url"]
                print(f"  Yahoo参考URL: {yahoo['url']}")
        else:
            print("  Yahoo: 取得済みスキップ")

        # データ保存（ステータスは変更しない）
        if result:
            save_urls(page_id, result)
            print(f"  → データ保存（ステータス未変更）\n")
        else:
            print(f"  取得データなし・スキップ\n")

        item_results[page_id] = (result, props)
        time.sleep(1)

    # ── Step 2: 記事タイトルでグループ化 ──
    groups: dict[str, list[tuple[str, dict, dict]]] = {}
    for page in items:
        page_id = page["id"]
        props   = page["properties"]
        title   = get_text(props.get("記事タイトル"))
        result, _ = item_results.get(page_id, ({}, {}))
        groups.setdefault(title, []).append((page_id, result, props))

    # ── Step 3: グループごとに完了判定・一括ステータス更新 ──
    print("=" * 50)
    print("記事ごとの完了判定")
    print("=" * 50)

    for title, group in groups.items():
        label = f"「{title[:40]}」" if title else "（タイトルなし）"
        all_ok = all(is_fully_fetched(r, p) for _, r, p in group)

        if all_ok:
            print(f"✅ {label} 全{len(group)}件 → 完了に一括更新")
            for page_id, _, _ in group:
                mark_complete(page_id)
        else:
            missing = sum(1 for _, r, p in group if not is_fully_fetched(r, p))
            print(f"⏳ {label} {missing}/{len(group)}件 未取得 → 全件未処理のまま")

    print("\n全件処理完了")


if __name__ == "__main__":
    main()
