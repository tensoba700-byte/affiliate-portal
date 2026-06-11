#!/usr/bin/env python3
import os
import sys
import json
import re

# プロジェクトルートを取得
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(project_root, "scripts"))

def get_article_title(slug: str) -> str:
    """比較記事のMarkdownファイルからタイトルを取得する。"""
    article_path = os.path.join(project_root, "src", "content", "articles", f"{slug}.md")
    if os.path.exists(article_path):
        try:
            with open(article_path, "r", encoding="utf-8") as f:
                content = f.read()
                # フロントマターから title を取得
                match = re.search(r'^title:\s*["\']?(.*?)["\']?\s*$', content, re.MULTILINE)
                if match:
                    return match.group(1).strip()
        except Exception as e:
            print(f"⚠️ 比較記事 {slug} のタイトル取得中にエラー: {e}")
    return "あわせて読みたいおすすめ比較記事"

def run_publish():
    # 1. validate_column_draft による検証
    try:
        from validate_column_draft import validate
    except ImportError as e:
        print(f"❌ バリデータ (validate_column_draft.py) のインポートに失敗しました: {e}")
        sys.exit(1)
        
    print("⏳ コラムドラフトのバリデーションを実行中...")
    if not validate():
        print("❌ バリデーションに失敗したため、パブリッシュを中止します。")
        sys.exit(1)
        
    draft_path = os.path.join(project_root, "column_draft.json")
    if not os.path.exists(draft_path):
        print(f"❌ {draft_path} が見つかりません。")
        sys.exit(1)
        
    try:
        with open(draft_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        print(f"❌ column_draft.json のパースに失敗しました: {e}")
        sys.exit(1)
        
    meta = data.get("meta", {})
    content = data.get("content", {})
    related_articles = data.get("related_articles", [])
    
    slug = meta.get("slug")
    title = meta.get("title")
    category = meta.get("category")
    publish_date = meta.get("publish_date")
    description = meta.get("description")
    
    lead = content.get("lead", "")
    sections = content.get("sections", [])
    faq = content.get("faq", [])
    summary = content.get("summary", "")
    
    # 2. Markdownの組み立て
    markdown_lines = []
    markdown_lines.append("---")
    markdown_lines.append(f'title: "{title}"')
    markdown_lines.append(f'description: "{description}"')
    markdown_lines.append(f'category: "{category}"')
    markdown_lines.append(f'publishDate: "{publish_date}"')
    markdown_lines.append("---")
    markdown_lines.append("")
    markdown_lines.append(lead)
    markdown_lines.append("")
    
    for sec in sections:
        markdown_lines.append(f"## {sec.get('heading')}")
        markdown_lines.append(sec.get('body', ''))
        markdown_lines.append("")
        
    if faq:
        markdown_lines.append("## ❓ よくある質問（FAQ）")
        markdown_lines.append("")
        for item in faq:
            markdown_lines.append(f"### {item.get('question')}")
            markdown_lines.append(item.get('answer', ''))
            markdown_lines.append("")
            
    markdown_lines.append("## 💬 まとめ")
    markdown_lines.append(summary)
    markdown_lines.append("")
    
    # related_articles があれば本文末尾に該当比較記事への内部リンクを挿入
    if related_articles:
        markdown_lines.append("---")
        markdown_lines.append("")
        markdown_lines.append("**あわせて読みたいおすすめ比較記事**")
        for r_slug in related_articles:
            r_title = get_article_title(r_slug)
            markdown_lines.append(f"- [{r_title}](/articles/{r_slug})")
        markdown_lines.append("")
        
    markdown_content = "\n".join(markdown_lines)
    
    # 3. " of " 最終チェック
    if " of " in markdown_content:
        print("❌ エラー: 出力文字列に日本語破損表現である ' of ' が検出されました。")
        print("パブリッシュを中止します。")
        sys.exit(1)
        
    # 4. ファイルへの書き出し
    columns_dir = os.path.join(project_root, "src", "content", "columns")
    os.makedirs(columns_dir, exist_ok=True)
    
    output_path = os.path.join(columns_dir, f"{slug}.md")
    try:
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(markdown_content)
        print(f"🎉 完了！コラムを正常に出力しました: {output_path}")
    except Exception as e:
        print(f"❌ ファイルの書き込みに失敗しました: {e}")
        sys.exit(1)

if __name__ == "__main__":
    run_publish()
