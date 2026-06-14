#!/usr/bin/env python3
import os
import sys
import re
import argparse
from datetime import datetime, timedelta
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

# プロジェクトルートを取得
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(project_root, ".env.local"))

def parse_markdown(file_path):
    """Markdownファイルからフロントマターと本文を分離してパースする。"""
    if not os.path.exists(file_path):
        print(f"❌ File not found: {file_path}")
        return None, None
        
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
        
    meta = {}
    body = content
    
    match = re.match(r"^---\s*\n(.*?)\n---\s*\n(.*)$", content, re.DOTALL)
    if match:
        front_matter = match.group(1)
        body = match.group(2)
        
        for line in front_matter.split("\n"):
            if ":" in line:
                key, val = line.split(":", 1)
                meta[key.strip()] = val.strip().strip('"').strip("'")
                
    return meta, body

def extract_summary_paragraphs(body: str, max_paragraphs=3) -> str:
    """本文から見出しやHTMLを除外した最初の数段落をプレーンテキストで抽出する。"""
    paragraphs = [p.strip() for p in body.split("\n\n") if p.strip()]
    
    selected = []
    for p in paragraphs:
        # 見出し、HTMLタグ、画像、水平線、単なるリンクブロックなどはスキップ
        if p.startswith("#") or p.startswith("<") or p.startswith("---") or p.startswith("!") or p.startswith("["):
            continue
            
        # HTMLタグの除去
        p_clean = re.sub(r'<[^>]+>', '', p)
        # Markdown太字の除去
        p_clean = re.sub(r'\*\*([^*]+)\*\*', r'\1', p_clean)
        # Markdownリンクのクリーンアップ: [テキスト](URL) -> テキスト
        p_clean = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', p_clean)
        
        if p_clean.strip():
            selected.append(p_clean.strip())
            
        if len(selected) >= max_paragraphs:
            break
            
    return "\n\n".join(selected)

def find_today_column():
    """今日（JST）公開されるコラムを探す。"""
    # 日本時間（UTC+9）の現在日付を取得
    # GitHub Actions等の環境を考慮してUTC時間に+9時間する
    jst_now = datetime.utcnow() + timedelta(hours=9)
    today_str = jst_now.strftime("%Y-%m-%d")
    print(f"Searching for columns scheduled for JST today: {today_str}")
    
    columns_dir = os.path.join(project_root, "src", "content", "columns")
    if not os.path.exists(columns_dir):
        print(f"❌ Columns directory not found: {columns_dir}")
        return None
        
    for fname in os.listdir(columns_dir):
        if not fname.endswith(".md") or fname == ".gitkeep":
            continue
            
        fpath = os.path.join(columns_dir, fname)
        meta, _ = parse_markdown(fpath)
        if meta and "publishDate" in meta:
            pub_date = meta["publishDate"]
            if pub_date.startswith(today_str):
                print(f"🎉 Found matching column: {fname} (scheduled at {pub_date})")
                return fpath
                
    print("ℹ️ No columns found for today.")
    return None

def fill_react_textarea(page, selector, value):
    """Reactが管理するtextareaに確実に値をバインドさせるためのハック"""
    js_code = """
    (args) => {
        const el = document.querySelector(args.selector);
        if (!el) return false;
        const setter = Object.getOwnPropertyDescriptor(window.HTMLTextAreaElement.prototype, "value").set;
        setter.call(el, args.value);
        el.dispatchEvent(new Event('input', { bubbles: true }));
        el.dispatchEvent(new Event('change', { bubbles: true }));
        el.dispatchEvent(new Event('blur', { bubbles: true }));
        return true;
    }
    """
    return page.evaluate(js_code, {"selector": selector, "value": value})

def post_to_note(file_path, dry_run=False):
    """note.com へ記事を投稿する。"""
    meta, body = parse_markdown(file_path)
    if not meta or not body:
        print("❌ Failed to parse column file.")
        return False
        
    title = meta.get("title")
    eyecatch = meta.get("eyecatch")
    slug = meta.get("slug")
    if not slug:
        slug = os.path.splitext(os.path.basename(file_path))[0]
        
    if not title:
        print("❌ Column title is missing.")
        return False
        
    # 本文（要約）の抽出とフッター組み立て（URLは別で入力するため分ける）
    summary = extract_summary_paragraphs(body, max_paragraphs=3)
    if not summary:
        print("❌ Failed to extract content summary.")
        return False
        
    post_intro = f"{summary}\n\n▼続きはこちらから読めるよ\n"
    import time
    post_url = f"https://www.mikke-style.com/column/{slug}?t={int(time.time())}"
    
    # 環境変数の読み込み
    email = os.getenv("NOTE_EMAIL")
    password = os.getenv("NOTE_PASSWORD")
    if not email or not password:
        print("❌ NOTE_EMAIL or NOTE_PASSWORD not set in environment.")
        return False
        
    # 見出し画像のパス
    image_path = ""
    if eyecatch:
        image_path = os.path.join(project_root, "public", eyecatch.lstrip("/"))
        if not os.path.exists(image_path):
            print(f"⚠️ Eyecatch image not found at: {image_path}")
            image_path = ""
            
    print(f"--- Posting Summary ---")
    print(f"Title: {title}")
    print(f"Image: {image_path if image_path else 'None'}")
    print(f"Body Intro:\n{post_intro}")
    print(f"URL: {post_url}")
    print(f"----------------------")
    
    with sync_playwright() as p:
        print("Launching browser...")
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        )
        page = context.new_page()
        
        try:
            print("Logging in to note.com...")
            page.goto("https://note.com/login")
            page.wait_for_timeout(3000)
            
            page.fill('input[placeholder*="mail@example.com"]', email)
            page.fill('input[type="password"]', password)
            page.locator('button:has-text("ログイン")').click()
            page.wait_for_timeout(5000)
            
            if "login" in page.url:
                print("❌ Login failed. Still on the login page.")
                browser.close()
                return False
                
            print("Navigating to new note editor...")
            page.goto("https://note.com/notes/new")
            page.wait_for_timeout(5000)
            
            # タイトルの入力
            print("Typing title...")
            fill_react_textarea(page, 'textarea[placeholder="記事タイトル"]', title)
            page.wait_for_timeout(1000)
            
            # 本文の入力
            print("Typing content...")
            editor_el = page.locator('div.ProseMirror[contenteditable="true"]')
            editor_el.focus()
            page.keyboard.type(post_intro)
            page.wait_for_timeout(500)
            
            # URLを入力
            print("Typing URL...")
            page.keyboard.type(post_url)
            page.wait_for_timeout(500)
            
            # Enterキーを2回押してリンクカード化をトリガー
            print("Pressing Enter twice to trigger link card...")
            page.keyboard.press("Enter")
            page.wait_for_timeout(500)
            page.keyboard.press("Enter")
            page.wait_for_timeout(4000)  # リンクカード生成処理待ち
            
            # 見出し画像のアップロード
            if image_path:
                print(f"Uploading cover image: {image_path}")
                page.locator('button[aria-label="画像を追加"]').click()
                page.wait_for_selector('button:has-text("画像をアップロード")')
                
                with page.expect_file_chooser() as fc_info:
                    page.locator('button:has-text("画像をアップロード")').click()
                file_chooser = fc_info.value
                file_chooser.set_files(image_path)
                
                print("Waiting for crop modal...")
                page.wait_for_selector('.CropModal__overlay', timeout=20000)
                
                # モーダル内の「保存」ボタンをクリック
                save_btn = page.locator('.CropModal__overlay button:has-text("保存")')
                save_btn.wait_for(state="visible", timeout=5000)
                page.wait_for_timeout(1500)  # アニメーション待ち
                save_btn.click()
                print("Clicked crop save button. Waiting for modal to close...")
                
                page.wait_for_selector('.CropModal__overlay', state="hidden", timeout=10000)
                print("Crop modal closed. Waiting for upload processing...")
                page.wait_for_timeout(4000)  # ローディング待機
                
            # 「下書き保存」をクリックして確実に同期させる
            print("Clicking '下書き保存' for synchronization...")
            page.locator('button:has-text("下書き保存"), button:has-text("一時保存")').click()
            page.wait_for_timeout(4000)  # 保存のネットワークリクエスト完了を待つ
            
            if dry_run:
                print("ℹ️ Dry-run mode enabled. Exiting before publishing.")
                browser.close()
                return True
                
            print("Clicking '公開に進む'...")
            page.locator('button:has-text("公開に進む")').click()
            
            # 投稿確認ポップアップが表示されるのを待つ
            print("Waiting for publishing settings screen...")
            page.wait_for_selector('button:has-text("投稿する"), button:has-text("更新する")', timeout=15000)
            page.wait_for_timeout(2000)
            
            # ハッシュタグの自動付与
            category = meta.get("category", "")
            tags_to_add = ["みっけ", "みっけ編集部"]
            if category == "haircare":
                tags_to_add.extend(["ヘアケア", "コスメ", "美容"])
            else:
                tags_to_add.extend(["スキンケア", "コスメ", "美容"])
                
            print(f"Adding hashtags: {tags_to_add}")
            try:
                for tag in tags_to_add:
                    tag_input = page.locator('input[placeholder*="ハッシュタグを追加"]')
                    if tag_input.count() > 0 and tag_input.first.is_visible():
                        tag_input.first.focus()
                        tag_input.first.fill(tag)
                        page.wait_for_timeout(500)
                        tag_input.first.press("Enter")
                        page.wait_for_timeout(1000)
                        print(f"Added hashtag: {tag}")
                    else:
                        print(f"⚠️ Hashtag input is not visible for tag: {tag}")
            except Exception as tag_err:
                print(f"⚠️ Failed to add hashtags: {tag_err}")
            
            # 実際に投稿する
            print("Clicking '投稿する' / '更新する'...")
            page.locator('button:has-text("投稿する"), button:has-text("更新する")').first.click()
            
            print("Waiting for publication to complete...")
            # 投稿完了後、リダイレクトを待つ
            page.wait_for_timeout(6000)
            
            published_url = page.url
            print(f"🎉 Successfully posted! URL: {published_url}")
            
            # 結果のログ出力用
            os.makedirs(os.path.join(project_root, "scratch"), exist_ok=True)
            with open(os.path.join(project_root, "scratch", "last_note_published.txt"), "w", encoding="utf-8") as f:
                f.write(published_url)
                
            browser.close()
            return True
            
        except Exception as e:
            print(f"❌ Error occurred during note posting: {e}")
            # エラー発生時の状態デバッグ用にスクショを保存
            try:
                os.makedirs(os.path.join(project_root, "scratch"), exist_ok=True)
                page.screenshot(path=os.path.join(project_root, "scratch", "error_post_state.png"))
                print("Saved error screenshot to scratch/error_post_state.png")
            except Exception:
                pass
            browser.close()
            return False

def main():
    parser = argparse.ArgumentParser(description="Auto post columns to note.com")
    parser.add_argument("--file", help="Path to specific column markdown file to post")
    parser.add_argument("--dry-run", action="store_true", help="Only save as draft and exit without publishing")
    args = parser.parse_args()
    
    target_file = None
    if args.file:
        target_file = os.path.abspath(args.file)
        print(f"Manual mode: Targeting specific file: {target_file}")
    else:
        print("Auto mode: Searching scheduled column for today...")
        target_file = find_today_column()
        
    if not target_file:
        print("No target file to process. Exiting.")
        sys.exit(0)
        
    success = post_to_note(target_file, dry_run=args.dry_run)
    if success:
        print("🎉 Note posting script completed successfully.")
        sys.exit(0)
    else:
        print("❌ Note posting script failed.")
        sys.exit(1)

if __name__ == "__main__":
    main()
