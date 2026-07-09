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

def split_sentences(text):
    """文末の文字で分割し、空でない文を返す。"""
    sentences = re.split(r'(?<=[。！？])', text)
    return [s.strip() for s in sentences if s.strip()]

def format_paragraph(text):
    """テキストを最大3文ずつの段落に分割してリストで返す。"""
    sentences = split_sentences(text)
    paragraphs = []
    for i in range(0, len(sentences), 3):
        chunk = "".join(sentences[i:i+3])
        paragraphs.append(chunk)
    return paragraphs

def ensure_single_bold(text):
    """段落内に太字が1箇所だけ存在することを保証する。無ければ自動で付与する。"""
    bolds = re.findall(r'\*\*([^*]+)\*\*', text)
    if bolds:
        first_bold = bolds[0]
        text_no_bold = text.replace(f"**{first_bold}**", first_bold)
        text_no_bold = re.sub(r'\*\*([^*]+)\*\*', r'\1', text_no_bold)
        return text_no_bold.replace(first_bold, f"**{first_bold}**", 1)
    else:
        keywords = [
            "導入美容液", "美容液", "スキンケア", "化粧水", "洗顔", "浸透", 
            "使い方", "タイミング", "効果", "水分", "摩擦", "成分", "角層", 
            "バリア機能", "うるおい", "皮脂", "毛穴", "クレンジング", "乾燥"
        ]
        for kw in keywords:
            if kw in text:
                return text.replace(kw, f"**{kw}**", 1)
        
        brackets = re.findall(r'[「『]([^」』]+)[」』]', text)
        if brackets:
            first_bracket = brackets[0]
            return text.replace(f"「{first_bracket}」", f"**「{first_bracket}」**", 1)
            
        kanji_seqs = re.findall(r'[\u4e00-\u9faf]{3,}', text)
        if kanji_seqs:
            first_kanji = kanji_seqs[0]
            return text.replace(first_kanji, f"**{first_kanji}**", 1)
            
        return text

def build_note_content(body: str) -> str:
    """Markdown本文から見出しと段落をパースし、note用ライティングルールに基づいて構成する。"""
    lines = body.split("\n")
    intro_paragraphs = []
    headings = [] # (title, paragraphs) のリスト
    
    current_heading = None
    current_paragraphs = []
    in_intro = True
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        if line.startswith("<") or line.startswith("---") or line.startswith("!") or line.startswith("[") or line.startswith("###"):
            continue
            
        if line.startswith("## "):
            in_intro = False
            if current_heading:
                headings.append((current_heading, current_paragraphs))
            current_heading = line.replace("## ", "").strip()
            current_paragraphs = []
        elif line.startswith("#"):
            continue
        else:
            if in_intro:
                intro_paragraphs.append(line)
            else:
                if current_heading:
                    current_paragraphs.append(line)
                    
    if current_heading:
        headings.append((current_heading, current_paragraphs))
        
    note_sections = []
    
    intro_text_chunks = []
    for p in intro_paragraphs[:2]:
        formatted = format_paragraph(p)
        for chunk in formatted:
            intro_text_chunks.append(ensure_single_bold(chunk))
    if intro_text_chunks:
        note_sections.append("\n\n".join(intro_text_chunks))
    
    count = 0
    for title, paras in headings:
        if count >= 3:
            break
        if not paras:
            continue
            
        sec_title = f"## {title}"
        formatted_paras = format_paragraph(paras[0])
        sec_body = ensure_single_bold(formatted_paras[0])
        
        note_sections.append(f"{sec_title}\n\n{sec_body}")
        count += 1
        
    filtered_sections = [s for s in note_sections if s.strip()]
    return "\n\n---\n\n".join(filtered_sections)

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
        
    candidates = []
    for fname in os.listdir(columns_dir):
        if not fname.endswith(".md") or fname == ".gitkeep":
            continue
            
        fpath = os.path.join(columns_dir, fname)
        meta, _ = parse_markdown(fpath)
        if meta and "publishDate" in meta:
            pub_date = meta["publishDate"]
            if pub_date.startswith(today_str):
                if "noteUrl" in meta:
                    print(f"ℹ️ Column already published to note (has noteUrl): {fname}")
                    continue
                candidates.append((pub_date, fpath, fname))
                
    if candidates:
        candidates.sort(key=lambda x: x[0])
        pub_date, fpath, fname = candidates[0]
        print(f"🎉 Found matching column to post: {fname} (scheduled at {pub_date})")
        return fpath
                
    print("ℹ️ No columns found to post for today.")
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
    note_content = build_note_content(body)
    if not note_content:
        print("❌ Failed to build note content.")
        return False
        
    import time
    post_url = f"https://www.mikke-style.com/column/{slug}?t={int(time.time())}"
    full_content = f"{note_content}\n\n---\n\n▼続きはこちらから読めるよ\n{post_url}"
    
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
    print(f"Full Content:\n{full_content}")
    print(f"----------------------")
    
    state_path = os.path.join(project_root, "scratch", "state.json")
    
    with sync_playwright() as p:
        print("Launching browser...")
        browser = p.chromium.launch(headless=True)
        
        # Load existing state.json if available
        if os.path.exists(state_path):
            print(f"Loading existing session from {state_path}...")
            context = browser.new_context(
                storage_state=state_path,
                user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
            )
        else:
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
            )
            
        page = context.new_page()
        
        try:
            # Check if we need to log in
            print("Navigating to new note editor...")
            page.goto("https://note.com/notes/new")
            page.wait_for_timeout(3000)
            
            if "login" in page.url:
                print("Session expired or not logged in. Logging in to note.com...")
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
                
                # Save new session state
                os.makedirs(os.path.dirname(state_path), exist_ok=True)
                context.storage_state(path=state_path)
                print(f"🎉 Saved new session state to {state_path}")
                
                # Go back to editor page
                page.goto("https://note.com/notes/new")
                page.wait_for_timeout(5000)
            
            # タイトルの入力
            print("Typing title...")
            fill_react_textarea(page, 'textarea[placeholder="記事タイトル"]', title)
            page.wait_for_timeout(1000)
            
            # 本文とURLの入力
            print("Typing content and URL...")
            editor_el = page.locator('div.ProseMirror[contenteditable="true"]')
            editor_el.focus()
            page.keyboard.insert_text(full_content)
            page.wait_for_timeout(1500)
            
            # Enterキーを2回押してリンクカード化をトリガー
            print("Pressing Enter twice to trigger link card...")
            page.keyboard.press("Enter")
            page.wait_for_timeout(1500)
            page.keyboard.press("Enter")
            page.wait_for_timeout(6000)  # リンクカード生成処理待ち
            
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
            
            # Markdownファイルを更新して noteUrl を追加
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                
                parts = content.split("---", 2)
                if len(parts) >= 3:
                    front_matter = parts[1]
                    body = parts[2]
                    
                    if "noteUrl:" not in front_matter:
                        if not front_matter.endswith("\n"):
                            front_matter += "\n"
                        front_matter += f"noteUrl: \"{published_url}\"\n"
                        
                        new_content = f"---{front_matter}---{body}"
                        with open(file_path, "w", encoding="utf-8") as f:
                            f.write(new_content)
                        print(f"📝 Updated front matter of {file_path} with noteUrl.")
            except Exception as fe:
                print(f"⚠️ Failed to update markdown with noteUrl: {fe}")
                
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
