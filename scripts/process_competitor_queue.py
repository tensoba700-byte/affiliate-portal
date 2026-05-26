import os
import sys
import requests
import urllib.parse
from dotenv import load_dotenv

# プロジェクトルートのパスを追加
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from generate_from_competitor import generate_from_competitor

def search_notion_database(headers, db_name):
    """Notion内から指定された名前のデータベースを検索してIDを返します。"""
    url = "https://api.notion.com/v1/search"
    payload = {
        "query": db_name,
        "filter": {"property": "object", "value": "database"}
    }
    try:
        res = requests.post(url, headers=headers, json=payload, timeout=10)
        if res.status_code == 200:
            results = res.json().get("results", [])
            for db in results:
                # タイトルの一致を確認
                title_arr = db.get("title", [])
                if title_arr and title_arr[0].get("plain_text") == db_name:
                    return db["id"]
    except Exception as e:
        print(f"⚠️ Notion検索エラー: {e}")
    return None

def update_page_status(headers, page_id, status_name):
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
        requests.patch(url, headers=headers, json=payload, timeout=10)
    except Exception as e:
        print(f"⚠️ ステータス更新エラー: {e}")

def main():
    load_dotenv(".env.local")
    NOTION_API_KEY = os.getenv("NOTION_API_KEY")

    if not NOTION_API_KEY:
        print("❌ エラー: .env.local 内に NOTION_API_KEY が設定されていません。")
        sys.exit(1)

    headers = {
        "Authorization": f"Bearer {NOTION_API_KEY}",
        "Notion-Version": "2022-06-28",
        "Content-Type": "application/json"
    }

    db_name = "みっけ！競合記事キュー"
    print(f"🔍 Notion内からデータベース 「{db_name}」 を探索中...")
    db_id = search_notion_database(headers, db_name)

    if not db_id:
        print(f"\n💡 【データベースが見つかりませんでした】")
        print(f"Notion上で新しいデータベースを作成し、以下の通り設定してください。")
        print(f"1. データベース名: {db_name}")
        print(f"2. カラム設定:")
        print(f"   - Name (タイトル形式): 記事のキーワードやメモ用")
        print(f"   - URL (URL形式): 競合サイトのURLを入力")
        print(f"   - Status (セレクト形式): 選択肢として「未処理」「処理中」「完了」「エラー」を作成")
        print(f"   - Category (セレクト形式): 選択肢として「生活雑貨」「ガジェット」「インテリア」「美容・スキンケア」「便利グッズ」を作成（省略時はガジェット）")
        print(f"3. 作成後、Notionインテグレーション（みっけ！）にこのデータベースへのアクセス権限を共有してください。")
        sys.exit(2)

    print(f"✅ データベース発見！ ID: {db_id}")

    # 「未処理」ステータスの競合記事情報を最古順で1件取得
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

    res = requests.post(f"https://api.notion.com/v1/databases/{db_id}/query", headers=headers, json=payload, timeout=10)
    if res.status_code != 200:
        print(f"❌ Notionデータベースクエリ失敗: {res.status_code} {res.text}")
        sys.exit(1)

    results = res.json().get("results", [])
    if not results:
        print("ℹ️ 「未処理」の競合記事URLはありません。処理をスキップします。")
        sys.exit(2)

    page = results[0]
    page_id = page["id"]
    props = page["properties"]

    # 競合URLの取得
    url_prop = props.get("URL", {})
    competitor_url = url_prop.get("url") or ""

    if not competitor_url:
        print("⚠️ 警告: 選択された行の URL が空です。ステータスを「エラー」に更新します。")
        update_page_status(headers, page_id, "エラー")
        sys.exit(1)

    # カテゴリの取得
    cat_prop = props.get("Category", {})
    category = cat_prop.get("select", {}).get("name", "ガジェット")

    print(f"\n🚀 処理開始: {competitor_url} (Category: {category})")
    
    # ステータスを「処理中」に更新
    update_page_status(headers, page_id, "処理中")

    try:
        # 記事の生成実行
        slug = generate_from_competitor(competitor_url, default_category=category)
        if slug:
            print(f"🎉 記事の自動生成に成功しました！ Slug: {slug}")
            # ステータスを「完了」に更新
            update_page_status(headers, page_id, "完了")
        else:
            print("❌ 記事の生成に失敗しました。")
            update_page_status(headers, page_id, "エラー")
            sys.exit(1)
    except Exception as e:
        print(f"❌ 処理中に例外が発生しました: {e}")
        update_page_status(headers, page_id, "エラー")
        sys.exit(1)

if __name__ == "__main__":
    main()
