#!/usr/bin/env python3
import os
import sys
import json
import re
import datetime
import subprocess
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv

# .env.local ロード
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(project_root, ".env.local"))

def fetch_url_text_puppeteer(url: str) -> str:
    """Puppeteerを使ってヘッドレスブラウザでHTMLを動的に取得し、本文を抽出して返します。"""
    js_code = r"""
const puppeteer = require('puppeteer');
(async () => {
  const browser = await puppeteer.launch({
    headless: true,
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });
  const page = await browser.newPage();
  await page.setUserAgent('Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/120.0.0.0');
  try {
    await page.goto(process.argv[2], { waitUntil: 'domcontentloaded', timeout: 35000 });
    await new Promise(r => setTimeout(r, 3000));
    
    // セレクタを待つ
    await page.waitForSelector('article, .sg-entry-content, main', { timeout: 15000 });

    const text = await page.evaluate(() => {
      // 記事本文のコンテナ
      const el = document.querySelector('article, .sg-entry-content, main');
      if (!el) return document.body.textContent;
      
      // 不要要素を削除
      const clone = el.cloneNode(true);
      const excludes = clone.querySelectorAll('script, style, iframe, .related-ranking, .buying-guide-recommend, .buying-guide-related');
      excludes.forEach(e => e.remove());
      
      return clone.textContent;
    });
    console.log(text);
  } catch (e) {
    console.error(e);
    process.exit(1);
  } finally {
    await browser.close();
  }
})();
"""
    temp_js_path = os.path.join(project_root, "puppeteer_column_temp.js")
    try:
        with open(temp_js_path, "w", encoding="utf-8") as f:
            f.write(js_code)
            
        res = subprocess.run(
            ['node', temp_js_path, url],
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='ignore'
        )
        if res.returncode == 0:
            return res.stdout
        else:
            print(f"⚠️ Puppeteer実行エラー: {res.stderr}")
            return ""
    except Exception as e:
        print(f"⚠️ Puppeteer呼び出し失敗: {e}")
        return ""
    finally:
        if os.path.exists(temp_js_path):
            try:
                os.remove(temp_js_path)
            except Exception:
                pass

def fetch_url_text_requests(url: str) -> str:
    """requests + BeautifulSoupを使ってHTMLを取得し、本文を抽出して返します。"""
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/120.0.0.0"
    }
    try:
        resp = requests.get(url, headers=headers, timeout=15)
        if resp.status_code != 200:
            print(f"⚠️ HTTPエラー: {resp.status_code} on {url}")
            return ""
            
        soup = BeautifulSoup(resp.text, 'html.parser')
        
        # サイトごとの最適化セレクタ
        selectors = [
            '.column-detail__body', # michill
            '.article-body-wrapper', # 美的
            '.article-body', # MAQUIA
            '.mery-article-body', # MERY
            '[itemprop="articleBody"]', # All About
            'article',
            'main'
        ]
        
        main_el = None
        for sel in selectors:
            main_el = soup.select_one(sel)
            if main_el:
                break
                
        if not main_el:
            main_el = soup.body
            
        # 不要タグ除外
        for tag in main_el.select('script, style, iframe, .related-link, .recommend-box, .writer-info, .related-post, .ranking-box, .article-footer'):
            tag.decompose()
            
        return main_el.get_text()
    except Exception as e:
        print(f"⚠️ requests取得エラー: {e}")
        return ""

def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/prepare_column.py <URL1> <URL2> ...")
        sys.exit(1)
        
    urls = sys.argv[1:]
    
    # Gemini APIキーチェック
    gemini_api_key = os.getenv("GEMINI_API_KEY")
    if not gemini_api_key:
        print("❌ エラー: GEMINI_API_KEY が .env.local に設定されていません。")
        sys.exit(1)
        
    import google.generativeai as genai
    genai.configure(api_key=gemini_api_key)
    
    stockpile_path = os.path.join(project_root, "column_stockpile.json")
    
    # 既存のストックパイル読み込み
    stockpile = []
    if os.path.exists(stockpile_path):
        try:
            with open(stockpile_path, "r", encoding="utf-8") as f:
                stockpile = json.load(f)
        except Exception as e:
            print(f"⚠️ 既存ストックパイルのパース失敗 (新規作成します): {e}")

    for url in urls:
        print(f"\n==================== Processing: {url} ====================")
        
        # 1. 本文テキストの抽出
        text = ""
        if "my-best.com" in url:
            print("Using Puppeteer for my-best...")
            text = fetch_url_text_puppeteer(url)
        else:
            print("Using requests + BeautifulSoup...")
            text = fetch_url_text_requests(url)
            
        if not text or len(text.strip()) < 100:
            print(f"❌ 本文抽出に失敗したか、テキストが短すぎます: {len(text) if text else 0}文字")
            continue
            
        print(f"抽出された本文サイズ: {len(text)} 文字. Geminiで事実抽出を実行します...")

        # 2. Gemini Flash による事実抽出 (Geminiは抽出専用・執筆禁止)
        prompt = f"""あなたは美容コラムの事実抽出器です。入力されたWeb記事のテキストから、美容・スキンケアに関する客観的事実・知識・手順・メカニズム・注意点・季節要因のみを抽出してください。

【抽出する事実の例】
- 洗顔時のすすぎ湯は30〜32度前後のぬるま湯が適している。
- レチノールはシワ改善に効果的だが、紫外線で分解されやすいため夜の使用が推奨される。
- エアコンの風は空気を乾燥させ、肌のバリア機能を低下させる。

【絶対禁止事項（抽出してはならないもの）】
- 具体的な商品名、ブランド名、メーカー名、店舗名（例: 「オルビス」「無印良品」「キュレル」など）。一切含めないでください。
- 「ランキング」「第◯位」「おすすめ人気商品」といった比較・ランキング表現。
- 広告、PR、販促的な文言。
- 執筆や記事の要約（「〜という記事です」などの説明は不要）。

【出力フォーマット】
以下のJSONフォーマットのみを出力してください。マークダウンによるコードブロック装飾（```json や ```）は一切含めず、純粋なJSON文字列のみを返してください。

{{
  "facts": [
    "事実1",
    "事実2",
    "事実3"
  ]
}}

【入力Web記事テキスト】
{text}
"""
        
        try:
            model = genai.GenerativeModel("models/gemini-2.5-flash")
            response = model.generate_content(prompt)
            
            # JSONクリーンアップとデコード
            response_text = response.text.strip()
            # もしマークダウンのコードブロックが含まれていたら剥ぐ
            response_text = re.sub(r'^```json\s*|^```\s*|```$', '', response_text, flags=re.MULTILINE).strip()
            
            facts_data = json.loads(response_text)
            facts = facts_data.get("facts", [])
            
            if not facts:
                print("⚠️ 事実リストが空です。")
                continue
                
            print(f"✅ 事実抽出に成功: {len(facts)} 件の事実を抽出しました。")
            
            # 既存の同一URLデータを削除（上書きマージのため）
            stockpile = [item for item in stockpile if item.get("url") != url]
            
            # 追加
            stockpile.append({
                "url": url,
                "fetched_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "facts": facts
            })
            
        except Exception as e:
            print(f"❌ Geminiによる事実抽出でエラーが発生しました: {e}")
            continue

    # 保存
    try:
        with open(stockpile_path, "w", encoding="utf-8") as f:
            json.dump(stockpile, f, ensure_ascii=False, indent=2)
        print(f"\n🎉 完了！ストックパイルを保存しました: {stockpile_path}")
    except Exception as e:
        print(f"❌ ストックパイルの保存失敗: {e}")

if __name__ == "__main__":
    main()
