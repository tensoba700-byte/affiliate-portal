from publish_article import run_publish, get_notion_data, generate_content_with_llm, json, datetime, slugify

def custom_publish(article_title, slug):
    print(f"🚀 Custom Processing: {article_title}")
    products = get_notion_data(article_title)
    if not products:
        print("No products found.")
        return False
    
    category = "家電"
    output_title = article_title.replace("2024", "2026")
    
    raw = generate_content_with_llm(products, output_title)
    if not raw:
        print("LLM generation failed.")
        return False
    
    data = json.loads(raw)
    
    # Build Markdown
    markdown = f"--- \ntitle: \"{output_title}\"\ncoverImage: \"\"\nexcerpt: \"{data['excerpt']}\"\npublishDate: \"{datetime.datetime.now().strftime('%Y-%m-%d')}\"\ncategory: \"{category}\"\n---\n\n{data['intro']}\n\n## ✅ 選び方のポイント\n<ul>" + "".join([f"<li>{p}</li>" for p in data['points']]) + "</ul>\n\n"
    
    for i, p in enumerate(data['products']):
        rank = i + 1
        notion_p = next((x for x in products if x['name'].lower() in p['name'].lower() or p['name'].lower() in x['name'].lower()), None)
        
        markdown += f"### 👑 第{rank}位: {p['name']}\n"
        if notion_p and notion_p['image_url']:
            markdown += f"IMAGE: {notion_p['image_url']}\n"
        
        markdown += f"[総合評価: {p['score']}]\n\n"
        
        if notion_p:
            for platform in ['amazon', 'rakuten', 'yahoo']:
                price = notion_p.get(f'{platform}_price')
                if price: markdown += f"{platform.upper()}_PRICE: {price}\n"
            for platform, key in [('amazon', 'asin'), ('rakuten', 'rakuten'), ('yahoo', 'yahoo')]:
                url = notion_p.get(f'{platform}_url')
                if url: markdown += f"{key.upper()}: {url}\n"
        
        formatted_desc = p['description'].replace('\\n', '\n\n')
        markdown += f"\n{formatted_desc}\n\n[AMAZON_LINK_HERE] [RAKUTEN_LINK_HERE] [YAHOO_LINK_HERE]\n\n:::pro\n" + "\n".join([f"- {m}" for m in p['pros']]) + "\n:::\n:::con\n" + "\n".join([f"- {c}" for c in p['cons']]) + "\n:::\n\n👤 **こんな人におすすめ**: " + p.get('recommended_for', '') + "\n\n"
    
    markdown += f"## 💬 まとめ\n{data['summary']}\n"
    
    path = f"/Users/tsukika/Desktop/affiliate-portal/src/content/articles/{slug}.md"
    with open(path, 'w', encoding='utf-8') as f:
        f.write(markdown)
    
    print(f"✅ Published: {path}")
    return True

if __name__ == "__main__":
    title = "【2026年最新】忙しい朝を劇的に変える！暮らしの質が上がる「厳選時短家電」5選"
    # Re-calculate slug to match what I used for the image
    import re
    def get_slug(text):
        text = text.replace("2024", "2026")
        text = re.sub(r'[^\w\s-]', '', text).strip().lower()
        text = re.sub(r'[-\s]+', '-', text)
        date_prefix = datetime.datetime.now().strftime("%Y%m%d")
        return f"{date_prefix}-{text[:30]}"
    
    slug = get_slug(title)
    custom_publish(title, slug)
