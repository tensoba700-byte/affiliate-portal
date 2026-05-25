import os
import re
import datetime

def disperse_article_dates():
    articles_dir = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "src", "content", "articles"
    )
    if not os.path.exists(articles_dir):
        print(f"❌ Articles directory not found: {articles_dir}")
        return

    articles = []
    for fn in os.listdir(articles_dir):
        if not fn.endswith(".md") or fn == "GENERATION_RULES.md":
            continue
        
        full_path = os.path.join(articles_dir, fn)
        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            m = re.search(r'publishDate:\s*["\']?(\d{4}-\d{2}-\d{2})', content)
            if m:
                p_date = datetime.datetime.strptime(m.group(1), "%Y-%m-%d").date()
            else:
                p_date = datetime.date(2026, 4, 12)
                
            # If the parsed date is before 2026 (like the 2024 one), we adjust it to 2026 for sorting
            if p_date.year < 2026:
                p_date = datetime.date(2026, 4, 12)
                
            articles.append({
                "filename": fn,
                "path": full_path,
                "original_date": p_date,
                "content": content
            })
        except Exception as e:
            print(f"⚠️ Error reading {fn}: {e}")

    if not articles:
        print("ℹ️ No articles found.")
        return

    # Sort primarily by original date, secondarily by filename/slug for deterministic ordering
    articles.sort(key=lambda x: (x["original_date"], x["filename"]))

    # We start dispersing consecutively starting from 2026-03-01 so that they are nicely distributed in 2026
    start_date = datetime.date(2026, 3, 1)
    print(f"📅 Start date set to: {start_date}")
    print(f"🔄 Dispersing {len(articles)} articles consecutively...")

    current_date = start_date
    updated_count = 0

    for idx, art in enumerate(articles):
        expected_date_str = current_date.strftime("%Y-%m-%d")
        
        # Replace the entire publishDate line
        new_content = re.sub(
            r'publishDate:\s*.*',
            f'publishDate: "{expected_date_str}"',
            art["content"]
        )
        
        if new_content != art["content"]:
            try:
                with open(art["path"], 'w', encoding='utf-8') as f:
                    f.write(new_content)
                print(f"✅ {art['filename']}: ➡️ {expected_date_str}")
                updated_count += 1
            except Exception as e:
                print(f"❌ Error writing {art['filename']}: {e}")
        else:
            print(f"⚪ {art['filename']}: {expected_date_str} (unchanged)")
            
        current_date += datetime.timedelta(days=1)

    print(f"\n🎉 Finished! Dispersed {len(articles)} articles. Updated {updated_count} files.")

if __name__ == "__main__":
    disperse_article_dates()
