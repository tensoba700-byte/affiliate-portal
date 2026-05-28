#!/usr/bin/env python3
import os
import re
import glob

# Paths
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ARTICLES_DIR = os.path.join(ROOT_DIR, "src/content/articles")
EYECATCH_DIR = os.path.join(ROOT_DIR, "public/eyecatch")
CONFIG_PATH = os.path.join(ROOT_DIR, "next.config.ts")

# 削除対象リスト（スラッグ名）
DELETE_SLUGS = [
    "20260427-2026年片付け上手になれる見せる収納隠す収納おす",
    "20260428-台所に手間をかけない道具を共働き家庭の時短キッチン",
    "20260428-肌に正直なものだけを乾燥肌敏感肌のスキンケアアイテ",
    "20260429-思考が加速する机の話在宅ワーカーのデスク文具6選",
    "20260430-在宅ワークの肩こりに本気の回答を筋膜ケアボディリカ",
    "20260502-家をもっと賢くするスマートホームデバイス6選",
    "20260502-料理人が静かに選ぶ本物の道具燕三条関産の本格キッチ",
    "20260503-料理人が静かに選ぶ本物の道具燕三条関産の本格キッチ",
    "20260503-深い眠りには静かな準備がある睡眠の質を高める寝室入",
    "20260508-書くことがもっと好きになるこだわりデスク文具6選",
    "20260512-湯船でほどける夜に疲れた日の入浴グッズバスケア6選",
    "20260518-体を動かすのが楽しくなってきたフィットネスボディケ",
    "20260519-ながら聴きをもっと豊かにワイヤレスイヤホン-こだわ",
    "20260520-夜空の下へ持ち出したいアウトドアキャンプギア6選",
    "20260522-音で彩る自分だけの朝ポータブルスピーカーbluet",
    "20260524-日常に小さな贅沢を重ねる収納上手なスタッキングマグ6選",
    "20260524-肌は夜に育てる30代から始めるメンズスキンケア夜ル",
    "20260525-灯を落としてから肌と向き合う夜就寝前ナイトケアコス"
]

def main():
    # 1. すべてのMarkdownファイルを読み込み、削除対象と残存対象に分類する
    md_files = glob.glob(os.path.join(ARTICLES_DIR, "*.md"))
    
    all_articles = []
    for fpath in md_files:
        if os.path.basename(fpath) == "GENERATION_RULES.md":
            continue
            
        with open(fpath, "r", encoding="utf-8") as f:
            content = f.read()
            
        slug = os.path.basename(fpath).replace(".md", "")
        
        # frontmatter
        fm_match = re.match(r"^---\s*\n(.*?)\n---\s*\n", content, re.DOTALL)
        if not fm_match:
            continue
        fm_text = fm_match.group(1)
        
        cat_match = re.search(r"category:\s*[\"']?(.*?)[\"']?(?:\n|$)", fm_text)
        category = cat_match.group(1).strip() if cat_match else ""
        
        all_articles.append({
            "fpath": fpath,
            "slug": slug,
            "category": category
        })
        
    # 分類
    to_delete = [a for a in all_articles if a["slug"] in DELETE_SLUGS]
    remaining = [a for a in all_articles if a["slug"] not in DELETE_SLUGS]
    
    print(f"Loaded {len(all_articles)} articles.")
    print(f"To Delete: {len(to_delete)}")
    print(f"Remaining: {len(remaining)}")
    
    # カテゴリごとの優良な残存記事 (手動執筆・高品質なもの) をデフォルトとして特定する
    # 美容・スキンケア, ガジェット, インテリア, 生活雑貨, 便利グッズ
    default_redirects = {
        "美容・スキンケア": "20260526-best-shampoos-for-damaged-hair",
        "ガジェット": "20260526-mac-mini-monitors",
        "インテリア": "20260429-部屋に余白を置く一人暮らしミニマリストのインテリア",
        "生活雑貨": "20260505-夜の空気を香りで塗り替えるルームフレグランス6選",
        "便利グッズ": "20260530-keyboards"
    }
    
    # 2. 各削除対象について、同じカテゴリーの一番新しくて高品質な残存記事へマッピングする
    redirect_map = {}
    for art in to_delete:
        cat = art["category"]
        
        # 同じカテゴリーの残存記事
        cat_rem = [r for r in remaining if r["category"] == cat]
        cat_rem.sort(key=lambda x: x["slug"], reverse=True) # 新しい順
        
        destination = ""
        # 特殊な手動執筆 stockpiled 記事がカテゴリー内にあればそれを優先する
        for r in cat_rem:
            # stockpiled 記事の判定 (5月下旬の高品質記事)
            if r["slug"] in ["20260526-best-shampoos-for-damaged-hair", "20260526-mac-mini-monitors", "20260529-aroma-diffusers", "20260529-hair-dryers", "20260530-keyboards", "20260530-frying-pans", "20260531-umbrellas"]:
                destination = r["slug"]
                break
                
        if not destination and cat_rem:
            destination = cat_rem[0]["slug"] # 一番新しい記事
            
        if not destination:
            destination = default_redirects.get(cat, "articles") # カテゴリのデフォルト、最悪記事一覧
            
        redirect_map[art["slug"]] = destination
        print(f"🔗 Map: {art['slug']} -> {destination} (Category: {cat})")
        
    # 3. 物理削除の実行 (Markdownファイルおよびアイキャッチ)
    deleted_count = 0
    for art in to_delete:
        # Markdown削除
        if os.path.exists(art["fpath"]):
            os.remove(art["fpath"])
            print(f"🗑️ Deleted article: {art['fpath']}")
            
        # アイキャッチHTML/PNG削除
        html_eye = os.path.join(EYECATCH_DIR, f"{art['slug']}.html")
        png_eye = os.path.join(EYECATCH_DIR, f"{art['slug']}.png")
        if os.path.exists(html_eye):
            os.remove(html_eye)
            print(f"🗑️ Deleted html eyecatch: {html_eye}")
        if os.path.exists(png_eye):
            os.remove(png_eye)
            print(f"🗑️ Deleted png eyecatch: {png_eye}")
        deleted_count += 1
        
    print(f"Successfully deleted {deleted_count} files.")
    
    # 4. next.config.ts への 301 リダイレクトの追加
    # ファイルを読み込み、redirects 配列の末尾に追記する
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        config_content = f.read()
        
    # redirects 配列の開始点と終了点をパース
    # `return [` から `];` の部分にリダイレクト定義を追加
    # すでに設定されているものをパースし、今回の18件を新たに追加
    redirect_rules_str = ""
    for src_slug, dest_slug in redirect_map.items():
        redirect_rules_str += f"""      {{
        source: '/articles/{src_slug}',
        destination: '/articles/{dest_slug}',
        permanent: true,
      }},
"""
    
    # next.config.ts 内の `];` の直前にリダイレクト定義を挿入する
    # 最後の `];` を見つけて、その手前に書き込む
    # 最後の `];` は redirects() メソッドの return の終わり
    match = re.search(r"(\s+)(\];\s*\}\s*,\s*\n\s*\};)", config_content)
    if match:
        spacing = match.group(1)
        suffix = match.group(2)
        
        # 置き換え
        modified_content = config_content.replace(match.group(0), spacing + redirect_rules_str.strip() + "\n" + spacing + "];\n  },\n};")
        
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            f.write(modified_content)
        print("✅ Added 301 redirects to next.config.ts successfully!")
    else:
        print("❌ Could not parse next.config.ts structure for redirect insertion.")

if __name__ == "__main__":
    main()
