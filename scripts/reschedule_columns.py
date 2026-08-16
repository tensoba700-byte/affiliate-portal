#!/usr/bin/env python3
import os
import re
import datetime

def reschedule_columns():
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    columns_dir = os.path.join(project_root, "src", "content", "columns")
    
    if not os.path.exists(columns_dir):
        print(f"❌ Columns directory not found: {columns_dir}")
        return

    columns = []
    for fn in os.listdir(columns_dir):
        if not fn.endswith(".md") or fn == ".gitkeep":
            continue
        
        full_path = os.path.join(columns_dir, fn)
        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # noteUrl の有無を確認
            has_note_url = False
            if re.search(r'^noteUrl:\s*["\']?(.*?)["\']?\s*$', content, re.MULTILINE):
                has_note_url = True
                
            # publishDate の取得
            m = re.search(r'publishDate:\s*["\']?([^"\']+)["\']?', content)
            p_date = None
            if m:
                date_str = m.group(1).strip()
                try:
                    p_date = datetime.datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
                except ValueError:
                    try:
                        p_date = datetime.datetime.strptime(date_str, "%Y-%m-%d")
                    except ValueError:
                        pass
            
            if not p_date:
                p_date = datetime.datetime(2000, 1, 1) # 日付がないものは古いものとして扱う
                
            columns.append({
                "filename": fn,
                "path": full_path,
                "has_note_url": has_note_url,
                "publish_date": p_date,
                "content": content
            })
        except Exception as e:
            print(f"⚠️ Error reading {fn}: {e}")

    # 未投稿のものだけをフィルタリング
    unpublished = [c for c in columns if not c["has_note_url"]]
    
    if not unpublished:
        print("ℹ️ No unpublished columns found.")
        return

    # 現在のpublishDateの古い順、同値ならファイル名順でソート
    unpublished.sort(key=lambda x: (x["publish_date"], x["filename"]))

    # 本日(2026-08-17)の12:00:00を起点にする
    start_dt = datetime.datetime(2026, 8, 17, 12, 0, 0)
    current_dt = start_dt
    
    print(f"📅 Start datetime set to: {start_dt}")
    print(f"🔄 Rescheduling {len(unpublished)} unpublished columns consecutively...")

    updated_count = 0

    for idx, col in enumerate(unpublished):
        expected_date_str = current_dt.strftime("%Y-%m-%d %H:%M:%S")
        
        # publishDate の行を置換
        new_content = re.sub(
            r'publishDate:\s*.*',
            f'publishDate: "{expected_date_str}"',
            col["content"]
        )
        
        if new_content != col["content"]:
            try:
                with open(col["path"], 'w', encoding='utf-8') as f:
                    f.write(new_content)
                print(f"✅ {col['filename']}: {col['publish_date'].strftime('%Y-%m-%d %H:%M:%S')} ➡️ {expected_date_str}")
                updated_count += 1
            except Exception as e:
                print(f"❌ Error writing {col['filename']}: {e}")
        else:
            print(f"⚪ {col['filename']}: {expected_date_str} (unchanged)")
            
        # 次のスロット計算
        if current_dt.hour == 12:
            current_dt = current_dt.replace(hour=22, minute=0, second=0)
        else:
            current_dt = current_dt + datetime.timedelta(days=1)
            current_dt = current_dt.replace(hour=12, minute=0, second=0)

    print(f"\n🎉 Finished! Rescheduled {len(unpublished)} columns. Updated {updated_count} files.")

if __name__ == "__main__":
    reschedule_columns()
