import os
import sys
import re
import time
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(project_root, ".env.local"))

sys.path.append(os.path.join(project_root, "scripts"))
from note_auto_post import parse_markdown, extract_summary_paragraphs

def fix_react_textarea(page, selector, value):
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

def fix_note_post(page, note_id, markdown_path):
    print(f"\n--- Fixing Note ID: {note_id} using {os.path.basename(markdown_path)} ---")
    meta, body = parse_markdown(markdown_path)
    if not meta or not body:
        print(f"❌ Failed to parse markdown: {markdown_path}")
        return False
        
    title = meta.get("title")
    slug = meta.get("slug")
    if not slug:
        slug = os.path.splitext(os.path.basename(markdown_path))[0]
        
    summary = extract_summary_paragraphs(body, max_paragraphs=3)
    if not summary:
        print("❌ Failed to extract summary.")
        return False
        
    # 重複タイトルなしの新しいフォーマット
    post_intro = f"{summary}\n\n▼続きはこちらから読めるよ\n"
    post_url = f"https://www.mikke-style.com/column/{slug}"
    
    edit_url = f"https://editor.note.com/notes/{note_id}/edit/"
    print(f"Navigating to editor: {edit_url}")
    page.goto(edit_url)
    page.wait_for_timeout(6000)
    
    try:
        # タイトルの入力値も一応確実にバインド
        fix_react_textarea(page, 'textarea[placeholder="記事タイトル"]', title)
        
        # 本文のProseMirror要素を取得してフォーカス
        editor_el = page.locator('div.ProseMirror[contenteditable="true"]')
        editor_el.focus()
        page.wait_for_timeout(500)
        
        # 全選択して削除
        print("Clearing editor content...")
        page.keyboard.press("Meta+A")
        page.wait_for_timeout(500)
        page.keyboard.press("Backspace")
        page.wait_for_timeout(1000)
        
        char_count_text = page.locator('aside:has-text("文字")').text_content()
        if "0 文字" not in char_count_text and char_count_text.strip() != "":
            print("Trying Control+A to clear...")
            page.keyboard.press("Control+A")
            page.wait_for_timeout(500)
            page.keyboard.press("Backspace")
            page.wait_for_timeout(1000)
            
        # 再入力
        print("Typing intro text...")
        page.keyboard.type(post_intro)
        page.wait_for_timeout(500)
        
        print("Typing URL...")
        page.keyboard.type(post_url)
        page.wait_for_timeout(500)
        
        print("Pressing Enter twice to trigger link card...")
        page.keyboard.press("Enter")
        page.wait_for_timeout(500)
        page.keyboard.press("Enter")
        page.wait_for_timeout(5000)  # カード化待機
        
        # 下書き/一時保存
        print("Saving draft...")
        page.locator('button:has-text("下書き保存"), button:has-text("一時保存")').click()
        page.wait_for_timeout(4000)
        
        # 公開に進む
        print("Clicking '公開に進む'...")
        page.locator('button:has-text("公開に進む")').click()
        page.wait_for_selector('button:has-text("投稿する"), button:has-text("更新する")', timeout=15000)
        page.wait_for_timeout(2000)
        
        # 再投稿する (更新する)
        print("Clicking '投稿する' / '更新する' to update post...")
        page.locator('button:has-text("投稿する"), button:has-text("更新する")').click()
        page.wait_for_timeout(6000)
        
        print(f"🎉 Note ID {note_id} updated successfully! Current URL: {page.url}")
        return True
        
    except Exception as e:
        print(f"❌ Error while updating note {note_id}: {e}")
        page.screenshot(path=os.path.join(project_root, "scratch", f"error_fix_{note_id}.png"))
        return False

def main():
    email = os.getenv("NOTE_EMAIL")
    password = os.getenv("NOTE_PASSWORD")
    
    if not email or not password:
        print("❌ NOTE_EMAIL or NOTE_PASSWORD not set in .env.local")
        return
        
    # 現在アクセス可能なエイジングケアコラム(na90b9ed584ea)だけをターゲットにする
    notes_to_fix = [
        ("na90b9ed584ea", os.path.join(project_root, "src", "content", "columns", "col-aging-care-when-to-start.md"))
    ]
    
    with sync_playwright() as p:
        print("Launching browser...")
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        )
        page = context.new_page()
        
        print("Logging in to note.com...")
        page.goto("https://note.com/login")
        page.wait_for_timeout(3000)
        page.fill('input[placeholder*="mail@example.com"]', email)
        page.fill('input[type="password"]', password)
        page.locator('button:has-text("ログイン")').click()
        page.wait_for_timeout(5000)
        
        for note_id, md_path in notes_to_fix:
            fix_note_post(page, note_id, md_path)
            
        browser.close()

if __name__ == "__main__":
    main()
