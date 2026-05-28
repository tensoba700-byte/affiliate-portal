#!/usr/bin/env python3
import os
import re
import glob

# Articles directory
ARTICLES_DIR = "src/content/articles"

def add_internal_links():
    # Find all Markdown files excluding GENERATION_RULES.md
    md_files = [f for f in glob.glob(os.path.join(ARTICLES_DIR, "*.md")) if os.path.basename(f) != "GENERATION_RULES.md"]
    
    articles = []
    for fpath in md_files:
        with open(fpath, "r", encoding="utf-8") as f:
            content = f.read()
            
        slug = os.path.basename(fpath).replace(".md", "")
        
        # Parse Frontmatter
        fm_match = re.match(r"^---\s*\n(.*?)\n---\s*\n", content, re.DOTALL)
        if not fm_match:
            continue
            
        fm_text = fm_match.group(1)
        body = content[fm_match.end():]
        
        title_match = re.search(r"title:\s*[\"']?(.*?)[\"']?(?:\n|$)", fm_text)
        cat_match = re.search(r"category:\s*[\"']?(.*?)[\"']?(?:\n|$)", fm_text)
        
        title = title_match.group(1).strip() if title_match else slug
        category = cat_match.group(1).strip() if cat_match else ""
        
        articles.append({
            "fpath": fpath,
            "slug": slug,
            "title": title,
            "category": category,
            "body": body,
            "frontmatter": fm_text
        })
        
    print(f"Loaded {len(articles)} articles.")
    
    # Update each article with related articles (3 to 5 articles from the same category)
    updated_count = 0
    for art in articles:
        if not art["category"]:
            continue
            
        # Select related articles (same category, different slug)
        # We sort by slug (which starts with publish date YYYYMMDD) descending to prefer newer articles
        related = [a for a in articles if a["slug"] != art["slug"] and a["category"] == art["category"]]
        related.sort(key=lambda x: x["slug"], reverse=True)
        
        # Take 3 to 5 articles (up to 5)
        related_subset = related[:5]
        if len(related_subset) < 3:
            # If there are less than 3 related articles in the same category, relax category filter or just take what we have
            # Since we have ~80 articles, there should be plenty in each category
            pass
            
        if not related_subset:
            continue
            
        # Create Related Articles Markdown Block
        rel_block = "\n\n---\n\n## 🌈 あわせて見たい関連記事\n"
        for r in related_subset:
            rel_block += f"- [{r['title']}](/articles/{r['slug']})\n"
            
        # Strip existing related articles blocks from body to avoid duplicates
        body_clean = re.sub(r"\n+---\n+## 🌈 あわせて見たい関連記事\n+[\s\S]*?$", "", art["body"])
        body_clean = re.sub(r"\n+---\n+## 関連記事\n+[\s\S]*?$", "", body_clean)
        
        body_clean = body_clean.strip()
        new_body = body_clean + rel_block
        
        # Write back to file
        new_content = f"---\n{art['frontmatter']}\n---\n\n{new_body}\n"
        with open(art["fpath"], "w", encoding="utf-8") as f:
            f.write(new_content)
        updated_count += 1
            
    print(f"Successfully reinforced internal links for {updated_count} articles!")

if __name__ == "__main__":
    add_internal_links()
