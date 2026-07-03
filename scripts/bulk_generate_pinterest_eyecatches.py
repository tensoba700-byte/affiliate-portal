import os
import sys
import glob
import re

# Resolve paths relative to this script
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(SCRIPT_DIR)

from publish_article import generate_pinterest_eyecatch_html, take_pinterest_eyecatch_screenshot, get_seasonal_catch_copy
from pinterest_auto_post import parse_markdown

def extract_images_from_markdown(file_path):
    images = []
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
    # Match lines like "IMAGE: https://..."
    matches = re.findall(r"^IMAGE:\s*(https?://\S+)", content, re.MULTILINE)
    return matches

def main():
    project_root = os.path.dirname(SCRIPT_DIR)
    articles_dir = os.path.join(project_root, "src", "content", "articles")
    
    if not os.path.exists(articles_dir):
        print(f"Error: Articles directory not found: {articles_dir}")
        return

    md_files = glob.glob(os.path.join(articles_dir, "*.md"))
    print(f"Found {len(md_files)} markdown files in total.")
    
    success_count = 0
    for f_path in md_files:
        basename = os.path.basename(f_path)
        slug = basename[:-3]
        
        # Exclude rules
        if slug in ["GENERATION_RULES", "COLUMN_RULES", "COLUMN_SCHEMA"]:
            continue
        if slug.endswith("-fix"):
            continue
            
        print(f"Processing: {slug}...")
        meta = parse_markdown(f_path)
        if not meta:
            print(f"  [Error] Failed to parse frontmatter")
            continue
            
        title = meta.get("title", "")
        category = meta.get("category", "")
        
        if not title or not category:
            print(f"  [Error] Missing title or category")
            continue
            
        image_urls = extract_images_from_markdown(f_path)
        
        # Generate Pinterest HTML
        generate_pinterest_eyecatch_html(
            slug=slug,
            title=title,
            category=category,
            image_urls=image_urls,
            catch_copy=get_seasonal_catch_copy(category)
        )
        
        # Screenshot
        success = take_pinterest_eyecatch_screenshot(slug)
        if success:
            success_count += 1
            
    print(f"\nCompleted! Generated {success_count} Pinterest eyecatch images successfully.")

if __name__ == "__main__":
    main()
