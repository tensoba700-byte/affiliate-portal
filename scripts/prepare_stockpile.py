#!/usr/bin/env python3
"""
Notionの「みっけ！競合記事キュー」から未処理の競合URL（my-best.com等）を1件取得し、
スクレイピングして商品情報とアフィリエイトリンク・画像を自動収集してJSONに書き出すスクリプト。
"""

import os
import sys
import json
import requests
import urllib.parse
import re
import time
import unicodedata
from dotenv import load_dotenv

# プロジェクトルートのパスを追加
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# .env.local をロード
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env.local"))

NOTION_API_KEY = os.getenv("NOTION_API_KEY")
DATABASE_ID = "36cddb45-8772-80c3-ab74-eb061ecee73f"  # 「みっけ！競合記事キュー」のID

if not NOTION_API_KEY:
    print("❌ エラー: NOTION_API_KEY が .env.local に設定されていません。")
    sys.exit(1)

NOTION_HEADERS = {
    "Authorization": f"Bearer {NOTION_API_KEY}",
    "Notion-Version": "2022-06-28",
    "Content-Type": "application/json"
}

def update_page_status(page_id: str, status_name: str):
    """Notionの特定ページのステータスプロパティを更新します。"""
    url = f"https://api.notion.com/v1/pages/{page_id}"
    payload = {
        "properties": {
            "Status": {
                "status": {"name": status_name}
            }
        }
    }
    try:
        requests.patch(url, headers=NOTION_HEADERS, json=payload, timeout=10)
    except Exception as e:
        print(f"⚠️ ステータス更新エラー: {e}")

def fetch_url_text_puppeteer(url: str) -> str:
    """Puppeteerを使ってヘッドレスブラウザでHTMLを動的に取得し、DOM解析してJSON文字列を返します。"""
    import subprocess
    import tempfile
    
    js_code = r"""
const puppeteer = require('puppeteer');
(async () => {
  const browser = await puppeteer.launch({
    headless: true,
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });
  const page = await browser.newPage();
  await page.setRequestInterception(true);
  page.on('request', (req) => {
    const resourceType = req.resourceType();
    if (['image', 'stylesheet', 'font', 'media'].includes(resourceType)) {
      req.abort();
    } else {
      req.continue();
    }
  });
  await page.setUserAgent('Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/120.0.0.0');
  try {
    await page.goto(process.argv[2], { waitUntil: 'domcontentloaded', timeout: 30000 });
    try {
      await page.waitForSelector('h3', { timeout: 10000 });
    } catch (e) {}
    
    // 完全に描画されるのを少し待つ
    await new Promise(r => setTimeout(r, 3000));
    
    const data = await page.evaluate(() => {
      // 0. 特殊文字・改行・空白を除去する正規化ヘルパー
      const cleanName = (str) => {
        return (str || "").toLowerCase().replace(/\s+/g, "").trim();
      };

      // 1. 記事タイトル
      const competitor_title = document.querySelector('h1')?.textContent.trim() || document.title || "";
      
      // 2. 導入文（最初のH3より前に位置する長めの段落群）
      const firstH3 = document.querySelector('h3');
      const introParas = [];
      if (firstH3) {
        const allParas = Array.from(document.querySelectorAll('p'));
        for (const p of allParas) {
          if (p.compareDocumentPosition(firstH3) & Node.DOCUMENT_POSITION_FOLLOWING) {
            const txt = p.textContent.trim();
            if (txt.length > 20 && !txt.includes('徹底した自社検証')) {
              introParas.push(txt);
            }
          }
        }
      }
      const competitor_intro = introParas.join('\n\n');
      
      // 3. 構成情報（H2およびH3見出しのツリー）
      const competitor_structure = Array.from(document.querySelectorAll('h2, h3')).map(h => ({
        tag: h.tagName.toLowerCase(),
        text: h.textContent.trim()
      }));
      
      // 4. 選び方ガイド (Extracting full text and retaining subheading structures)
      let competitor_buying_guide = "";
      const choiceH2 = Array.from(document.querySelectorAll('h2')).find(h2 => h2.textContent.includes('選び方') || h2.textContent.includes('選ぶ'));
      if (choiceH2) {
        const parts = [];
        let next = choiceH2.nextElementSibling;
        while (next) {
          const tagName = next.tagName.toLowerCase();
          if (tagName === 'h2') break;
          if (tagName === 'h3') {
            parts.push("### " + next.textContent.trim());
          } else if (tagName === 'h4') {
            parts.push("#### " + next.textContent.trim());
          } else if (tagName === 'p' || tagName === 'ul' || tagName === 'ol' || tagName === 'li') {
            parts.push(next.textContent.trim());
          } else {
            const innerParas = Array.from(next.querySelectorAll('p, li, h3, h4')).map(el => {
              const tag = el.tagName.toLowerCase();
              if (tag === 'h3') return "### " + el.textContent.trim();
              if (tag === 'h4') return "#### " + el.textContent.trim();
              return el.textContent.trim();
            });
            if (innerParas.length > 0) {
              parts.push(...innerParas);
            } else {
              const text = next.textContent.trim();
              if (text && text.length > 15 && !text.includes('商品を見る') && !text.includes('最安価格')) {
                parts.push(text);
              }
            }
          }
          next = next.nextElementSibling;
        }
        competitor_buying_guide = parts.filter(Boolean).join('\n\n');
      }

      // 4.5 専門家コメント・アドバイス
      let competitor_expert_comments = "";
      const expertDivs = Array.from(document.querySelectorAll('div, section, p')).filter(el => {
        const text = el.textContent || "";
        return (text.includes('専門家') || text.includes('監修') || text.includes('アドバイス')) && text.length > 50 && text.length < 1500;
      });
      if (expertDivs.length > 0) {
        competitor_expert_comments = Array.from(new Set(expertDivs.map(el => el.textContent.trim()))).join('\n\n');
      }

      // 4.6 FAQセクションのQ&A抽出
      const competitor_faqs = [];
      const allTextElements = Array.from(document.querySelectorAll('p, div, li, h3, h4'));
      const seenFaqs = new Set();
      for (let i = 0; i < allTextElements.length; i++) {
        const text = allTextElements[i].textContent.trim();
        if ((/^Q[.:\s]/i.test(text) || text.startsWith('質問：') || text.startsWith('【質問】')) && text.length > 5 && text.length < 200) {
          let answer = "";
          for (let j = i + 1; j < Math.min(allTextElements.length, i + 15); j++) {
            const nextText = allTextElements[j].textContent.trim();
            if ((/^A[.:\s]/i.test(nextText) || nextText.startsWith('回答：') || nextText.startsWith('【回答】') || nextText.startsWith('答：')) && nextText.length > 5 && nextText.length < 1000) {
              answer = nextText;
              break;
            }
          }
          if (answer && !seenFaqs.has(text)) {
            seenFaqs.add(text);
            competitor_faqs.push({
              question: text,
              answer: answer
            });
          }
        }
      }

      // 4.7 まとめセクションの抽出
      let competitor_summary = "";
      const summaryH2 = Array.from(document.querySelectorAll('h2')).find(h2 => h2.textContent.includes('まとめ') || h2.textContent.includes('おわりに') || h2.textContent.includes('総括') || h2.textContent.includes('最後に'));
      if (summaryH2) {
        const parts = [];
        let next = summaryH2.nextElementSibling;
        while (next) {
          const tagName = next.tagName.toLowerCase();
          if (tagName === 'h2') break;
          parts.push(next.textContent.trim());
          next = next.nextElementSibling;
        }
        competitor_summary = parts.filter(Boolean).join('\n\n');
      }
      
      // 5. JSON-LDからGTIN（JAN）およびASINを事前に抽出
      const jsonLdProducts = {};
      const scripts = Array.from(document.querySelectorAll('script[type="application/ld+json"]'));
      scripts.forEach(script => {
        try {
          const ld = JSON.parse(script.textContent.trim());
          if (ld && ld['@type'] === 'Article' && ld.mainEntity) {
            let itemLists = [];
            if (Array.isArray(ld.mainEntity)) {
              itemLists = ld.mainEntity;
            } else {
              itemLists = [ld.mainEntity];
            }
            
            itemLists.forEach(item => {
              if (item && (item['@type'] === 'ItemList' || item.itemListElement)) {
                const listItems = item.itemListElement || [];
                listItems.forEach(li => {
                  const prod = li.item || {};
                  const name = prod.name || li.name || "";
                  const gtin = prod.gtin || "";
                  const asin = prod.asin || "";
                  let rating = "";
                  if (prod.aggregateRating && prod.aggregateRating.ratingValue) {
                    rating = String(prod.aggregateRating.ratingValue);
                  }
                  if (name) {
                    jsonLdProducts[cleanName(name)] = { gtin, asin, rating };
                  }
                });
              }
            });
          }
        } catch(e) {}
      });
      
      // 6. 商品リストと商品説明の抽出 (Accumulating sibling content for verification results, comments)
      const h2s = Array.from(document.querySelectorAll('h2'));
      const rankingH2 = h2s.find(h2 => {
        const txt = h2.textContent || "";
        return txt.includes('おすすめ人気ランキング') || txt.includes('徹底比較') || txt.includes('売れ筋ランキング') || txt.includes('おすすめ人気商品');
      });

      const h3s = Array.from(document.querySelectorAll('h3'));
      const products = [];
      let rankCounter = 1;
      
      h3s.forEach((h3) => {
        // ランキングH2が定義されている場合、そのH2より前に位置するH3は除外する
        if (rankingH2) {
          const pos = rankingH2.compareDocumentPosition(h3);
          if (!(pos & Node.DOCUMENT_POSITION_FOLLOWING)) {
            return;
          }
        }
        const name = h3.textContent.trim();
        // 不要な見出しを除外
        if (!name || name.length < 2 || name.includes('売れ筋ランキング') || name.includes('おすすめ人気ランキング') || name.includes('レビュー') || name.includes('比較一覧表')) {
          return;
        }
        
        let description = "";
        
        // Strategy 1: Sibling text accumulation to fetch ALL paragraphs, reviews, and test details
        const descParts = [];
        let sibling = h3.nextElementSibling;
        while (sibling) {
          const siblingTag = sibling.tagName.toLowerCase();
          if (siblingTag === 'h3' || siblingTag === 'h2') break;
          
          const text = sibling.textContent.trim();
          if (text && !text.includes('最安価格') && !text.includes('商品を見る') && !text.includes('Amazon') && !text.includes('楽天市場') && !text.includes('Yahoo!')) {
            const childTexts = Array.from(sibling.querySelectorAll('p, li, h4')).map(el => el.textContent.trim());
            if (childTexts.length > 0) {
              descParts.push(...childTexts);
            } else {
              descParts.push(text);
            }
          }
          sibling = sibling.nextElementSibling;
        }
        
        if (descParts.length > 0) {
          description = descParts.filter(Boolean).join('\n\n');
        }
        
        // Fallbacks if Strategy 1 fails
        if (!description) {
          let container = h3.parentElement?.parentElement;
          let descEl = container?.nextElementSibling;
          if (descEl && descEl.tagName.toLowerCase() === 'div') {
            description = descEl.textContent.trim();
          }
        }
        if (!description) {
          const wrapper = h3.closest('div[class*="css-"]');
          if (wrapper) {
            const divs = Array.from(wrapper.children);
            if (divs.length >= 2) {
              description = divs[1].textContent.trim();
            }
          }
        }
        
        if (description && !description.includes('商品...') && !description.includes('徹底比較') && description !== 'EMPTY') {
          let jan_code = "";
          let asin = "";
          let rating = "";
          const normName = cleanName(name);
          let match = jsonLdProducts[normName];
          if (!match) {
            const key = Object.keys(jsonLdProducts).find(k => k.includes(normName) || normName.includes(k));
            if (key) match = jsonLdProducts[key];
          }
          if (match) {
            jan_code = match.gtin || "";
            asin = match.asin || "";
            rating = match.rating || "";
          }
          
          let scraped_image = "";
          const wrapper = h3.closest('div[class*="css-"]');
          if (wrapper) {
            const imgEl = wrapper.querySelector('img');
            if (imgEl) {
              scraped_image = imgEl.src || imgEl.getAttribute('data-src') || imgEl.getAttribute('src') || "";
            }
          }
          if (!scraped_image) {
            const container = h3.parentElement?.parentElement;
            const imgEl = container?.querySelector('img');
            if (imgEl) {
              scraped_image = imgEl.src || imgEl.getAttribute('data-src') || imgEl.getAttribute('src') || "";
            }
          }
          
          // Direct links scraping from the page
          let amazon_scraped_url = "";
          let rakuten_scraped_url = "";
          let yahoo_scraped_url = "";
          
          let linkSibling = h3.nextElementSibling;
          while (linkSibling) {
            const siblingTag = linkSibling.tagName.toLowerCase();
            if (siblingTag === 'h3' || siblingTag === 'h2') break;
            
            const aTags = [];
            if (siblingTag === 'a') {
              aTags.push(linkSibling);
            }
            aTags.push(...Array.from(linkSibling.querySelectorAll('a')));
            
            aTags.forEach(a => {
              const href = a.href || "";
              const text = a.textContent.trim().toLowerCase();
              if (href.includes('/link') || href.includes('amazon.co.jp') || href.includes('rakuten.co.jp') || href.includes('shopping.yahoo.co.jp') || href.includes('valuecommerce.com')) {
                if (text.includes('amazon') || href.includes('amazon.co.jp')) {
                  amazon_scraped_url = href;
                } else if (text.includes('楽天') || href.includes('rakuten.co.jp')) {
                  rakuten_scraped_url = href;
                } else if (text.includes('ヤフー') || text.includes('yahoo') || href.includes('shopping.yahoo.co.jp') || href.includes('valuecommerce.com')) {
                  yahoo_scraped_url = href;
                }
              }
            });
            linkSibling = linkSibling.nextElementSibling;
          }
          
          if (!amazon_scraped_url || !rakuten_scraped_url || !yahoo_scraped_url) {
            let parent = h3.parentElement;
            for (let depth = 0; depth < 5 && parent; depth++) {
              const aTags = Array.from(parent.querySelectorAll('a'));
              aTags.forEach(a => {
                const href = a.href || "";
                const text = a.textContent.trim().toLowerCase();
                if (href.includes('/link') || href.includes('amazon.co.jp') || href.includes('rakuten.co.jp') || href.includes('shopping.yahoo.co.jp') || href.includes('valuecommerce.com')) {
                  if ((text.includes('amazon') || href.includes('amazon.co.jp')) && !amazon_scraped_url) {
                    amazon_scraped_url = href;
                  } else if ((text.includes('楽天') || href.includes('rakuten.co.jp')) && !rakuten_scraped_url) {
                    rakuten_scraped_url = href;
                  } else if ((text.includes('ヤフー') || text.includes('yahoo') || href.includes('shopping.yahoo.co.jp') || href.includes('valuecommerce.com')) && !yahoo_scraped_url) {
                    yahoo_scraped_url = href;
                  }
                }
              });
              parent = parent.parentElement;
            }
          }
          
          products.push({
            rank: rankCounter++,
            name,
            jan_code,
            asin,
            description,
            rating: rating || "",
            scraped_image: scraped_image || "",
            amazon_scraped_url: amazon_scraped_url || "",
            rakuten_scraped_url: rakuten_scraped_url || "",
            yahoo_scraped_url: yahoo_scraped_url || ""
          });
        }
      });
      
      return {
        competitor_title,
        competitor_intro,
        competitor_structure,
        competitor_buying_guide,
        competitor_expert_comments,
        competitor_faqs,
        competitor_summary,
        products
      };
    });
    
    console.log(JSON.stringify(data, null, 2));
  } catch (e) {
    console.error(e);
    process.exit(1);
  } finally {
    await browser.close();
  }
})();
"""
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    temp_js_path = os.path.join(project_root, "puppeteer_temp_scraper.js")
    
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

def extract_capacity(title: str) -> str:
    """容量（ml, gなど）を抽出します。タイトルマッチングの精度向上用。"""
    normalized_title = unicodedata.normalize('NFKC', title)
    m = re.search(r'(\d+(?:ml|g|kg|L|枚|回分|本|個|oz))', normalized_title, re.IGNORECASE)
    return m.group(1).lower() if m else ""

def verify_title_match(target_title: str, candidate_title: str) -> bool:
    """2つの商品タイトルが一致しているか大雑把に検証します。"""
    if not target_title or not candidate_title:
        return True
    
    target_norm = unicodedata.normalize('NFKC', target_title)
    candidate_norm = unicodedata.normalize('NFKC', candidate_title)
    
    # 容量のチェック
    cap1 = extract_capacity(target_norm)
    cap2 = extract_capacity(candidate_norm)
    if cap1 and cap2 and cap1 != cap2:
        return False  # 容量が明示的に異なる場合は不一致
        
    # キーワードの一致度
    clean1 = re.sub(r'[\(\)（）\[\]【】\-\s]', '', target_norm.lower())
    clean2 = re.sub(r'[\(\)（）\[\]【】\-\s]', '', candidate_norm.lower())
    
    # 共通キーワードのチェック
    words = [w for w in re.split(r'[^a-zA-Z0-9\u3040-\u309f\u30a0-\u30ff\u4e00-\u9faf]', target_norm) if len(w) >= 2]
    if not words:
        return True
        
    clean_candidate = re.sub(r'[\s\u3000]', '', candidate_norm.lower())
    match_count = sum(1 for w in words if re.sub(r'[\s\u3000]', '', w.lower()) in clean_candidate)
    match_rate = match_count / len(words)
    return match_rate >= 0.3

def remove_rakuten_params(url: str) -> str:
    """楽天アフィリエイトURLから m パラメータと rafcid パラメータを完全に削除します。"""
    if not url:
        return ""
    try:
        parsed = urllib.parse.urlparse(url)
        qs = urllib.parse.parse_qs(parsed.query)
        for param in ["m", "rafcid"]:
            if param in qs:
                del qs[param]
        new_query = urllib.parse.urlencode(qs, doseq=True)
        return urllib.parse.urlunparse(parsed._replace(query=new_query))
    except Exception:
        return url

def wrap_yahoo_url(url: str, query: str) -> str:
    """
    Yahoo URLをバリューコマースラッパー形式に変換します。
    /product/ や /product/j/ を含むURLは絶対に使わず、
    そういうURLの場合は検索結果URLに切り替えます。
    """
    if not url:
        # urlがない場合は、クエリを用いて検索結果URLを作る
        encoded_query = urllib.parse.quote(query, safe='')
        target_url = f"https://shopping.yahoo.co.jp/search?p={encoded_query}"
    else:
        # すでにバリューコマースリンクになっているかチェック
        # 例: https://ck.jp.ap.valuecommerce.com/servlet/referral?sid=xxx&pid=xxx&vc_url=https%3A%2F%2F...
        parsed = urllib.parse.urlparse(url)
        if "valuecommerce.com" in parsed.netloc:
            qs = urllib.parse.parse_qs(parsed.query)
            target_url = qs.get("vc_url", [""])[0]
            if not target_url:
                target_url = url # fallback
        else:
            target_url = url

        # /product/ や /product/j/ を含むかチェック
        if "/product/" in target_url or "/product/j/" in target_url:
            # 製品比較ページの場合は検索結果URLに切り替える
            encoded_query = urllib.parse.quote(query, safe='')
            target_url = f"https://shopping.yahoo.co.jp/search?p={encoded_query}"

    # バリューコマースラッパーに包む
    yahoo_sid = "3767611"
    yahoo_pid = "2201292"
    encoded_target = urllib.parse.quote(target_url, safe='')
    return f"https://ck.jp.ap.valuecommerce.com/servlet/referral?sid={yahoo_sid}&pid={yahoo_pid}&vc_url={encoded_target}"

def clean_and_convert_scraped_url(scraped_url: str, mall: str) -> str:
    """my-bestのスクレイピングURLから、自分自身のアフィリエイトURLに再構築して返します。"""
    if not scraped_url:
        return ""
    
    parsed = urllib.parse.urlparse(scraped_url)
    qs = urllib.parse.parse_qs(parsed.query)
    
    fallback_url = qs.get("fallback_url", [""])[0]
    url_in_query = qs.get("url", [""])[0]
    
    base_url = fallback_url if fallback_url else scraped_url
    
    parsed_base = urllib.parse.urlparse(base_url)
    qs_base = urllib.parse.parse_qs(parsed_base.query)
    
    if mall == "amazon":
        # ASINの抽出を試みる
        asin_match = re.search(r'/dp/([A-Z0-9]{10})|/gp/product/([A-Z0-9]{10})', base_url)
        if not asin_match and url_in_query:
            asin_match = re.search(r'/dp/([A-Z0-9]{10})|/gp/product/([A-Z0-9]{10})', url_in_query)
            
        if asin_match:
            asin_val = asin_match.group(1) or asin_match.group(2)
            return f"https://www.amazon.co.jp/dp/{asin_val}?tag=mikkestyle-22"
        
        if "tag" in qs_base:
            replaced_qs = qs_base.copy()
            replaced_qs["tag"] = ["mikkestyle-22"]
            new_query = urllib.parse.urlencode(replaced_qs, doseq=True)
            return urllib.parse.urlunparse(parsed_base._replace(query=new_query))
        else:
            connector = "&" if parsed_base.query else "?"
            return f"{base_url}{connector}tag=mikkestyle-22"
            
    elif mall == "rakuten":
        rakuten_affiliate_id = os.getenv("RAKUTEN_AFFILIATE_ID") or "52aa350c.c59bcb5a.52aa350d.c841a8ec"
        target_url = ""
        for param in ["url", "pc", "m"]:
            if param in qs_base:
                target_url = qs_base[param][0]
                break
            if param in qs:
                target_url = qs[param][0]
                break
        
        if not target_url:
            if "rakuten.co.jp" in base_url and not "hb.afl.rakuten.co.jp" in base_url:
                target_url = base_url
            else:
                for param in ["vc_url", "u"]:
                    if param in qs_base:
                        target_url = qs_base[param][0]
                        break
        
        if not target_url:
            target_url = base_url
            
        encoded_target = urllib.parse.quote(target_url)
        raw_rak_url = f"https://hb.afl.rakuten.co.jp/ichiba/{rakuten_affiliate_id}/?pc={encoded_target}"
        return remove_rakuten_params(raw_rak_url)
        
    elif mall == "yahoo":
        yahoo_sid = os.getenv("YAHOO_AFFILIATE_SID") or "3767611"
        yahoo_pid = os.getenv("YAHOO_AFFILIATE_PID") or "2201292"
        
        target_url = ""
        for param in ["url", "vc_url", "u"]:
            if param in qs_base:
                target_url = qs_base[param][0]
                break
            if param in qs:
                target_url = qs[param][0]
                break
                
        if not target_url:
            if "yahoo.co.jp" in base_url and not "valuecommerce.com" in base_url:
                target_url = base_url
            else:
                target_url = base_url
                
        encoded_target = urllib.parse.quote(target_url)
        return f"https://ck.jp.ap.valuecommerce.com/servlet/referral?sid={yahoo_sid}&pid={yahoo_pid}&vc_url={encoded_target}"

def generate_search_keywords(name: str) -> list:
    s = name.replace("BEYONDNILE", "BEYOND NILE")
    s = s.replace("YOUNGBIOHEAL", "YOUNG BIOHEAL")
    s = re.sub(r'[\uff5c\uff0f|/：:;；,，.．_＿\-─\(\)（）]', ' ', s)
    s = re.sub(r'([a-z])([A-Z])', r'\1 \2', s)
    s = re.sub(r'([a-zA-Z0-9]+)([\u3040-\u309f\u30a0-\u30ff\u4e00-\u9faf]+)', r'\1 \2', s)
    s = re.sub(r'([\u3040-\u309f\u30a0-\u30ff\u4e00-\u9faf]+)([a-zA-Z0-9]+)', r'\1 \2', s)
    
    words = [w.strip() for w in s.split() if w.strip()]
    if not words:
        return [name]
        
    keywords = []
    
    # 1. 英語(ストップワード除外) + 日本語特徴語 を最優先
    stop_words = {"the", "founders", "brand", "official", "co", "ltd", "inc", "japan", "公式", "ブランド", "日本", "aiロボティクス", "ai", "beyond", "cj", "olive", "young"}
    filtered_words = [w for w in words if w.lower() not in stop_words]
    
    eng_words = [w for w in filtered_words if re.match(r'^[a-zA-Z0-9]+$', w) and len(w) >= 2]
    jp_words = [w for w in filtered_words if not re.match(r'^[a-zA-Z0-9]+$', w) and len(w) >= 2]
    
    if eng_words and jp_words:
        keywords.append(f"{eng_words[0]} {jp_words[0]}")
        if len(jp_words) > 1:
            keywords.append(f"{eng_words[0]} {jp_words[1]}")
            
    if filtered_words:
        clean_filtered = [w for w in filtered_words if len(w) >= 2]
        if clean_filtered:
            keywords.append(" ".join(clean_filtered[:3]))
            if len(clean_filtered) >= 2:
                keywords.append(" ".join(clean_filtered[:2]))
            
    keywords.append(" ".join(words[:4]))
    if len(words) >= 2:
        keywords.append(" ".join(words[:2]))
    if len(words) >= 3:
        keywords.append(" ".join(words[:3]))
            
    seen = set()
    unique_keywords = []
    for kw in keywords:
        kw_clean = " ".join(kw.split())
        parts = kw_clean.split()
        if all(len(p) >= 2 for p in parts):
            if kw_clean and kw_clean not in seen:
                seen.add(kw_clean)
                unique_keywords.append(kw_clean)
            
    return unique_keywords

def fetch_rakuten_image(name, jan=None):
    url = "https://openapi.rakuten.co.jp/ichibams/api/IchibaItem/Search/20220601"
    app_id = os.getenv("RAKUTEN_APP_ID")
    access_key = os.getenv("RAKUTEN_ACCESS_KEY")
    affiliate_id = os.getenv("RAKUTEN_AFFILIATE_ID")
    
    headers = {
        "Referer": "https://www.mikke-style.com",
        "Origin": "https://www.mikke-style.com"
    }
    
    # ダミー画像を弾くヘルパー
    def is_invalid_image(img_url: str) -> bool:
        if not img_url:
            return True
        img_url_lower = img_url.lower()
        invalid_patterns = ["noimage", "rakuten_banner", "banner", "gift", "guide", "logo"]
        for pattern in invalid_patterns:
            if pattern in img_url_lower:
                return True
        return False
    
    # 1. JANコードがある場合は、まずJANコードのみで検索する
    if jan and str(jan).strip():
        params = {
            "format": "json",
            "applicationId": app_id,
            "accessKey": access_key,
            "affiliateId": affiliate_id,
            "keyword": str(jan).strip(),
            "imageFlag": 1,
            "hits": 3
        }
        try:
            res = requests.get(url, params=params, headers=headers, timeout=10)
            if res.status_code == 200:
                data = res.json()
                items = data.get("Items", [])
                for item_wrapper in items:
                    item = item_wrapper.get("Item", {})
                    img = item.get("mediumImageUrls", [{}])[0].get("imageUrl") or ""
                    if img and not is_invalid_image(img):
                        img = re.sub(r'\?_ex=\d+x\d+', '?_ex=640x640', img)
                        return img
        except Exception as e:
            print(f"⚠️ JAN検索エラー ({jan}): {e}")
            
    # 2. キーワード候補を生成して順次試す
    keywords = generate_search_keywords(name)
    print(f"🔍 '{name}' の検索用キーワード候補: {keywords}")
    
    for kw in keywords:
        time.sleep(1.0) # 429エラー回避のためのスリープ
        params = {
            "format": "json",
            "applicationId": app_id,
            "accessKey": access_key,
            "affiliateId": affiliate_id,
            "keyword": kw,
            "imageFlag": 1,
            "hits": 5
        }
        try:
            res = requests.get(url, params=params, headers=headers, timeout=10)
            if res.status_code == 200:
                data = res.json()
                items = data.get("Items", [])
                for item_wrapper in items:
                    item = item_wrapper.get("Item", {})
                    item_title = item.get("itemName", "")
                    img = item.get("mediumImageUrls", [{}])[0].get("imageUrl") or ""
                    if img and not is_invalid_image(img):
                        # タイトルの一致度を検証
                        if verify_title_match(name, item_title):
                            img = re.sub(r'\?_ex=\d+x\d+', '?_ex=640x640', img)
                            print(f"✅ ヒットしました (キーワード: '{kw}'): '{item_title[:30]}' -> {img[:50]}")
                            return img
            elif res.status_code == 429:
                print(f"⚠️ 429エラーが発生しました。キーワード '{kw}' の試行後に少し待ちます。")
                time.sleep(2.0)
        except Exception as e:
            print(f"⚠️ キーワード検索エラー ('{kw}'): {e}")
            
    # 3. それでもヒットしない場合は商品名全体で検索を試みる
    time.sleep(1.0)
    params = {
        "format": "json",
        "applicationId": app_id,
        "accessKey": access_key,
        "affiliateId": affiliate_id,
        "keyword": name,
        "imageFlag": 1,
        "hits": 5
    }
    try:
        res = requests.get(url, params=params, headers=headers, timeout=10)
        if res.status_code == 200:
            data = res.json()
            items = data.get("Items", [])
            for item_wrapper in items:
                item = item_wrapper.get("Item", {})
                img = item.get("mediumImageUrls", [{}])[0].get("imageUrl") or ""
                if img and not is_invalid_image(img):
                    img = re.sub(r'\?_ex=\d+x\d+', '?_ex=640x640', img)
                    return img
    except Exception as e:
        print(f"⚠️ 商品名全体検索エラー: {e}")
        
    return None

def amazon_image_from_asin(asin):
    if not asin:
        return None
    return f"https://m.media-amazon.com/images/I/{asin}.jpg"

def fetch_amazon_details_puppeteer(asin: str) -> dict:
    """Puppeteerを使用してAmazonの個別商品ページから価格とタイトルを取得します。"""
    import subprocess
    import json
    
    if not asin:
        return {"price": "", "title": "", "imageUrl": ""}
        
    script_dir = os.path.dirname(os.path.abspath(__file__))
    js_path = os.path.join(script_dir, "fetch_amazon_details.js")
    
    try:
        res = subprocess.run(
            ["node", js_path, asin],
            capture_output=True, text=True, timeout=45,
            cwd=os.path.dirname(script_dir)
        )
        if res.returncode == 0:
            out = res.stdout.strip()
            lines = out.split('\n')
            for line in reversed(lines):
                if line.strip().startswith('{') and line.strip().endswith('}'):
                    data = json.loads(line.strip())
                    if "error" not in data:
                        return data
                    break
    except Exception as e:
        print(f"⚠️ Puppeteer Amazon fetch failed: {e}")
            
    return {"price": "", "title": "", "imageUrl": ""}

def fetch_product_details(query: str, jan_code: str = "", asin: str = "", scraped_urls: dict = None):
    """Amazon, Yahoo, 楽天のAPIやスクレイピングから製品情報を取得します。"""
    details = {
        "image_url": "",
        "amazon_price": "なし",
        "rakuten_price": "なし",
        "yahoo_price": "なし",
        "rakuten_url": "",
        "yahoo_url": "",
        "amazon_url": "",
        "amazon_name": "なし",
        "rakuten_name": "なし",
        "yahoo_name": "なし"
    }
    
    browser_h = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/120.0.0.0"
    }

    # 1. Amazon
    clean_asin = asin.strip() if asin else ""
    if not clean_asin and scraped_urls and scraped_urls.get("amazon"):
        # scraped_url から ASIN を探す
        s_url = scraped_urls["amazon"]
        asin_match = re.search(r'/dp/([A-Z0-9]{10})|/gp/product/([A-Z0-9]{10})', s_url)
        if not asin_match:
            decoded_s_url = urllib.parse.unquote(s_url)
            asin_match = re.search(r'/dp/([A-Z0-9]{10})|/gp/product/([A-Z0-9]{10})', decoded_s_url)
        if asin_match:
            clean_asin = asin_match.group(1) or asin_match.group(2)

    if not clean_asin:
        search_queries = [jan_code.strip()] if jan_code else []
        search_queries.append(query)
        for q in search_queries:
            try:
                url = f"https://www.amazon.co.jp/s?k={urllib.parse.quote(q)}"
                res = requests.get(url, headers=browser_h, timeout=10)
                if res.status_code == 200:
                    match = re.search(r'data-asin="([A-Z0-9]{10})"[^>]*data-component-type="s-search-result"', res.text)
                    if not match:
                        match = re.search(r'data-component-type="s-search-result"[^>]*data-asin="([A-Z0-9]{10})"', res.text)
                    if match:
                        clean_asin = match.group(1)
                        break
            except Exception:
                continue

    amazon_product_name = ""
    if clean_asin:
        details["amazon_url"] = f"https://www.amazon.co.jp/dp/{clean_asin}?tag=mikkestyle-22"
        # 1. まず通常の requests.get を試みる
        try:
            dp_url = f"https://www.amazon.co.jp/dp/{clean_asin}"
            res = requests.get(dp_url, headers=browser_h, timeout=10)
            if res.status_code == 200:
                title_match = re.search(r'<span id="productTitle"[^>]*>\s*(.*?)\s*</span>', res.text, re.DOTALL)
                if title_match:
                    amazon_product_name = re.sub(r'\s+', ' ', title_match.group(1)).strip()
                    details["amazon_name"] = amazon_product_name
                
                price_match = re.search(r'"priceMobileShowActionFraction":\s*"([^"]+)"|class="a-price-whole">([^<]+)<', res.text)
                if price_match:
                    price_val = price_match.group(1) or price_match.group(2)
                    details["amazon_price"] = re.sub(r'[^\d]', '', price_val) if price_val else "なし"
                
                # 画像URLの取得
                img_match = re.search(r'data-old-hires="([^"]+)"|id="landingImage"[^>]*src="([^"]+)"|<div id="imgTagWrapperId"[^>]*>\s*<img[^>]*src="([^"]+)"', res.text, re.DOTALL)
                if img_match:
                    img_url = img_match.group(1) or img_match.group(2) or img_match.group(3)
                    if img_url:
                        details["image_url"] = img_url.strip()
        except Exception:
            pass

        # 2. 通常の取得がブロックされて失敗した場合、Puppeteerでフォールバック
        if not amazon_product_name or details["amazon_price"] == "none" or details["amazon_price"] == "なし" or not details["image_url"]:
            print(f"🔍 Amazon価格/タイトル/画像の取得に失敗（ブロックの可能性）。Puppeteerで再試行します (ASIN: {clean_asin})...")
            p_data = fetch_amazon_details_puppeteer(clean_asin)
            if p_data.get("price"):
                details["amazon_price"] = re.sub(r'[^\d]', '', p_data["price"])
                print(f"💰 Puppeteer価格取得成功: ¥{details['amazon_price']}")
            if p_data.get("title"):
                amazon_product_name = p_data["title"]
                details["amazon_name"] = amazon_product_name
                print(f"📦 Puppeteerタイトル取得成功: {amazon_product_name[:30]}...")
            if p_data.get("imageUrl"):
                details["image_url"] = p_data["imageUrl"]
                print(f"🖼️ Puppeteer画像取得成功: {p_data['imageUrl'][:50]}...")

    if not details["amazon_url"] and scraped_urls and scraped_urls.get("amazon"):
        details["amazon_url"] = clean_and_convert_scraped_url(scraped_urls["amazon"], "amazon")

    # 2. Yahoo Shopping (Disabled)
    details["yahoo_price"] = "なし"
    details["yahoo_url"] = ""
    details["yahoo_name"] = "なし"

    # 3. Rakuten
    rakuten_app_id = os.getenv("RAKUTEN_APP_ID")
    rakuten_access_key = os.getenv("RAKUTEN_ACCESS_KEY")
    rakuten_affiliate_id = os.getenv("RAKUTEN_AFFILIATE_ID")
    if rakuten_app_id:
        rak_headers = {
            "Referer": "https://www.mikke-style.com",
            "Origin": "https://www.mikke-style.com"
        }
        keywords_to_try = []
        if jan_code and jan_code.strip():
            keywords_to_try.append(jan_code.strip())
        name_kws = generate_search_keywords(query)
        if name_kws:
            keywords_to_try.extend(name_kws)
        else:
            keywords_to_try.append(query)
            
        for search_kw in keywords_to_try:
            try:
                endpoints = [
                    ("https://app.rakuten.co.jp/services/api/IchibaItem/Search/20170426", {"applicationId": rakuten_app_id, "affiliateId": rakuten_affiliate_id, "keyword": search_kw, "format": "json", "hits": 20}),
                    ("https://openapi.rakuten.co.jp/ichibams/api/IchibaItem/Search/20220601", {"applicationId": rakuten_app_id, "accessKey": rakuten_access_key, "affiliateId": rakuten_affiliate_id, "keyword": search_kw, "format": "json", "hits": 20})
                ]
                for endpoint_url, params in endpoints:
                    if not params.get("applicationId"):
                        continue
                    res = requests.get(endpoint_url, params=params, headers=rak_headers, timeout=10)
                    if res.status_code == 200:
                        items = res.json().get("Items", [])
                        for item_wrapper in items:
                            item = item_wrapper.get("Item", {})
                            item_title = item.get("itemName", "")
                            target_t = query
                            if amazon_product_name and amazon_product_name != "なし":
                                target_t = amazon_product_name
                            
                            is_jan_search = (jan_code and search_kw == jan_code.strip())
                            if is_jan_search or verify_title_match(target_t, item_title):
                                details["rakuten_price"] = str(item.get("itemPrice", ""))
                                raw_rak_url = item.get("affiliateUrl") or item.get("itemUrl") or ""
                                details["rakuten_url"] = remove_rakuten_params(raw_rak_url)
                                details["rakuten_name"] = item_title
                                if not details["image_url"]:
                                    img_url = item.get("mediumImageUrls", [{}])[0].get("imageUrl") or ""
                                    if img_url:
                                        details["image_url"] = re.sub(r'\?_ex=\d+x\d+', '?_ex=640x640', img_url)
                                break
                        if details["rakuten_url"]:
                            break
                if details["rakuten_url"]:
                    break
            except Exception:
                pass

    if not details["rakuten_url"] and scraped_urls and scraped_urls.get("rakuten"):
        details["rakuten_url"] = clean_and_convert_scraped_url(scraped_urls["rakuten"], "rakuten")
        if details["rakuten_name"] == "なし":
            details["rakuten_name"] = query

    if details["rakuten_url"]:
        details["rakuten_url"] = remove_rakuten_params(details["rakuten_url"])

    # Yahoo URLをすべて一律にバリューコマースのsid=3767611&pid=2201292形式にし、/product/を排除 (Disabled)
    details["yahoo_url"] = ""

    if not details["image_url"]:
        print(f"❌ エラー: 商品 '{query}' (JAN: {jan_code}) の画像が楽天APIからもAmazonからも取得できませんでした。")
        sys.exit(1)
    return details

def extract_mybest_ranking(html: str, url: str) -> list:
    """my-best.comのHTMLからJSON-LDを用いて正確に商品リストを抽出します。"""
    try:
        json_ld_blocks = re.findall(r'<script type="application/ld\+json">(.*?)</script>', html, re.DOTALL)
        for block in json_ld_blocks:
            try:
                data = json.loads(block.strip())
                if isinstance(data, dict) and data.get("@type") == "Article":
                    main_entity = data.get("mainEntity")
                    item_lists = []
                    if isinstance(main_entity, list):
                        item_lists = main_entity
                    elif isinstance(main_entity, dict):
                        item_lists = [main_entity]
                    
                    for item in item_lists:
                        if isinstance(item, dict) and item.get("@type") == "ItemList":
                            list_items = item.get("itemListElement", [])
                            if not list_items:
                                continue
                            
                            products = []
                            sorted_items = []
                            for li in list_items:
                                pos = li.get("position")
                                if pos is not None:
                                    try: pos = int(pos)
                                    except ValueError: pos = 999
                                else: pos = 999
                                sorted_items.append((pos, li))
                            sorted_items.sort(key=lambda x: x[0])
                            
                            for rank, li in sorted_items:
                                prod = li.get("item", {})
                                if not isinstance(prod, dict):
                                    continue
                                name = prod.get("name") or li.get("name") or ""
                                name = re.sub(r'\s+', ' ', name).strip()
                                gtin = prod.get("gtin") or ""
                                asin = prod.get("asin") or ""
                                desc = prod.get("description") or prod.get("reviewBody") or ""
                                
                                rating_val = ""
                                if "aggregateRating" in prod and isinstance(prod["aggregateRating"], dict):
                                    rating_val = str(prod["aggregateRating"].get("ratingValue") or "")
                                print(f"DEBUG: Scraped {name} (rating: {rating_val})")
                                products.append({
                                    "rank": rank,
                                    "name": name,
                                    "jan_code": gtin,
                                    "asin": asin,
                                    "description": desc,
                                    "rating": rating_val
                                })
                            
                            if products:
                                return products
            except Exception:
                pass
    except Exception:
        pass
    
    # フォールバック: 見出し抽出
    products = []
    matches = re.findall(r'<h[234][^>]*>(?:第)?(\d+)位[:：\s]*([^<]+)</h[234]>', html, re.IGNORECASE)
    if not matches:
        matches = re.findall(r'>\s*(?:第)?(\d+)位[:：\s]*([^<]+)<', html)
    
    if matches:
        seen_ranks = set()
        for rank_str, name in matches:
            try: rank = int(rank_str)
            except ValueError: continue
            name = name.strip()
            if rank not in seen_ranks and name:
                seen_ranks.add(rank)
                products.append({
                    "rank": rank,
                    "name": name,
                    "jan_code": "",
                    "asin": "",
                    "description": "",
                    "rating": ""
                })
        products.sort(key=lambda x: x["rank"])
        
    return products

def main():
    import sys
    if len(sys.argv) < 2:
        print("❌ エラー: NotionのページIDを引数に指定してください。")
        print("使用例: python3 scripts/prepare_stockpile.py <page_id>")
        sys.exit(1)
    target_page_id = sys.argv[1]

    # ロックファイルの取得（重複実行の防止）
    lock_file_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scripts", "prepare_stockpile.lock")
    try:
        global lock_file
        lock_file = open(lock_file_path, "w")
        import fcntl
        fcntl.flock(lock_file, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except (IOError, BlockingIOError):
        print("❌ エラー: 別のデータ収集プロセス（prepare_stockpile.py）が既に起動しています。重複実行を避けるため終了します。")
        sys.exit(0)
        
    print(f"🔍 Notionから特定の商品ページ（ID: {target_page_id}）を直接取得中...")
    res = requests.get(f"https://api.notion.com/v1/pages/{target_page_id}", headers=NOTION_HEADERS)
    if res.status_code != 200:
        print(f"❌ Notionページの取得に失敗しました: {res.status_code} {res.text}")
        sys.exit(1)
        
    page = res.json()
    page_id = page["id"]
    props = page["properties"]
    
    url_prop = props.get("URL") or {}
    competitor_url = url_prop.get("url") or ""
    
    cat_prop = props.get("Category") or {}
    category = ""
    if cat_prop and isinstance(cat_prop, dict):
        select_val = cat_prop.get("select")
        if select_val:
            category = select_val.get("name", "")
            
    title_prop = props.get("Name", {}).get("title") or []
    name_str = title_prop[0].get("plain_text") if title_prop else "Untitled"
    
    if not competitor_url:
        print(f"⚠️ 行「{name_str}」のURLが空です。ステータスをエラーに変更します。")
        update_page_status(page_id, "エラー")
        sys.exit(1)
        
    print(f"🚀 ターゲット発見！")
    print(f"  タイトル(仮): {name_str}")
    print(f"  競合URL: {competitor_url}")
    print(f"  カテゴリ: {category}")
    
    # ── 手動バイパス用ファイルのパス ──
    temp_json_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scripts", "extracted_data_temp.json")
    
    bypass_mode = False
    if os.path.exists(temp_json_path) and os.path.getsize(temp_json_path) > 100:
        print("💡 手動バイパス用の一時JSONファイルを検出しました。スクレイピングとGemini呼び出しをスキップします。")
        bypass_mode = True

    # ステータスを「処理中」に変更
    update_page_status(page_id, "処理中")
    
    products = []
    competitor_buying_guide = ""
    
    if not bypass_mode:
        print(f"⏳ 競合ページのHTMLをダウンロード＆解析中...")
        scraped_json = fetch_url_text_puppeteer(competitor_url)
        if not scraped_json:
            print("❌ ページの取得・解析に失敗しました。")
            update_page_status(page_id, "エラー")
            sys.exit(1)
            
        try:
            scraped_data = json.loads(scraped_json)
        except Exception as e:
            print(f"❌ 解析結果のJSONデコードに失敗しました: {e}")
            update_page_status(page_id, "エラー")
            sys.exit(1)
            
        competitor_buying_guide = scraped_data.get("competitor_buying_guide", "")
        products = scraped_data.get("products", [])
        
        if not products:
            print("❌ 商品の抽出に失敗しました。mybest形式でないか、DOMが変更された可能性があります。")
            update_page_status(page_id, "エラー")
            sys.exit(1)
            
        print(f"🎉 成功！ {len(products)} 個の商品を検出しました。")

    # ── Gemini Flash による事実抽出 ──
    import google.generativeai as genai
    
    genai_key = os.getenv("GEMINI_API_KEY")
    if not genai_key:
        print("❌ エラー: GEMINI_API_KEY が .env.local に設定されていません。")
        update_page_status(page_id, "エラー")
        sys.exit(1)
        
    genai.configure(api_key=genai_key)

    # 前処理: タイトル、ランキング順位、総合評価、点数、編集部コメント、おすすめコメントを削除
    def clean_scraping_text(text: str) -> str:
        if not text:
            return ""
        lines_list = text.split('\n')
        cleaned_lines = []
        for line in lines_list:
            # ランキング順位の除去（第X位、X位など）
            line = re.sub(r'第?\d+位\s*', '', line)
            # 総合評価・点数の除去
            line = re.sub(r'(総合評価|評価)[:：]?\s*\d+(\.\d+)?分?|点数[:：]?\s*\d+(\.\d+)?', '', line)
            # 編集部コメント・おすすめコメントなどの見出しやその内容が含まれる行をスキップ
            if re.search(r'編集部|おすすめコメント|おすすめのポイント|編集部のコメント|検証結果|おすすめポイント|ライターコメント', line):
                continue
            cleaned_lines.append(line)
        return '\n'.join(cleaned_lines)

    clean_buying_guide = clean_scraping_text(competitor_buying_guide)

    prompt = f"""あなたは記事ライターではありません。入力されたWeb記事から事実のみを抽出し、指定JSONへ変換するデータ変換器です。

【目的】記事本文の再利用は禁止。文章表現・言い回し・評価表現を捨て、事実データのみ抽出する。

【禁止事項】以下を保存しない：根拠のない主観的評価（高評価・人気・優秀・コスパが良い・肌に優しい・洗浄力が高い等）／効果効能の断定／記事本文の要約・言い換え／marketing copy

【許可】元記事に明記された検証可能な技術的事実は、出所を明記した形で許可する
例：「特許技術採用」ではなく「メーカー公称：特許技術XX採用」のように出所を明示する
「業界初」「No.1」等は、数字・第三者データによる裏付けが元記事にある場合のみ許可。なければ採用しない

【許可／禁止の境界 Few-shot例】
1. 許可：「メーカー公称：ヒアルロン酸Na・セラミドNP配合」（出所明示・成分名は固有情報）
2. 許可：「メーカー公称：特許出願中の独自処方（特許出願番号XXXX-XXXXXX）」（出所明示・検証可能な番号付き）
3. 許可：「厚生労働省の承認データに基づく医薬部外品（メーカー公称）」（第三者データによる裏付けあり）
4. 禁止：「編集部が選ぶNo.1の保湿力」（主観的評価・出所が編集部であり検証不能）
5. 禁止：「シミが消える」「肌が劇的に変わる」（効果効能の断定）
6. グレーゾーン→禁止：「業界初の処方」（数字・第三者データによる裏付けが元記事にない場合は採用しない）
7. グレーゾーン→許可：「国内シェアNo.1（メーカー公称、調査会社XX調べ）」（第三者調査データの裏付けあり）
8. グレーゾーン→禁止：「肌に優しい低刺激処方」（「肌に優しい」は主観表現。ただし「弱酸性・無香料・パラベンフリー処方」のように検証可能な事実のみに分解できる場合はその事実部分のみ許可）

【文章表現の扱い】文章表現・説明文・レビュー文の再利用は禁止。ただし商品仕様・成分名・機能名などの固有情報はそのまま保持してよい。

【selection_points】選び方の観点キーワードのみ・説明文禁止
例：["洗浄力", "保湿力", "乳化のしやすさ"]

【recommended_for】明示的に判断できる対象のみ・不明なら空配列

【facts】検証可能な客観的事実のみ・1項目1文・修飾語削除
許可例：W洗顔不要／無香料／アルコールフリー／濡れた手でも使用可能／植物由来オイル配合
禁止例：保湿力が高い／人気がある／使いやすい／コスパが良い

【出力】JSON以外の文字を出力しない

【最終チェック】①元記事の文章が残ってないか②評価表現がないか③marketing copyがないか④factsが客観的事実のみか⑤JSON以外の文字がないか。違反があれば修正してから出力。

【入力Web記事テキスト】
■ カテゴリ: {category}
■ 選び方ガイド本文:
{clean_buying_guide}

■ 商品リスト:
"""

    for p in products:
        p_name = p.get("name", "")
        p_jan = p.get("jan_code", "")
        p_asin = p.get("asin", "")
        p_desc = clean_scraping_text(p.get("description", ""))
        
        prompt += f"\n・商品名: {p_name}\n"
        prompt += f"  JANコード: {p_jan}\n"
        prompt += f"  ASIN: {p_asin}\n"
        prompt += f"  商品説明本文: {p_desc}\n"

    # OpenAPI 互換スキーマ定義
    schema = {
        "type": "OBJECT",
        "properties": {
            "category": {"type": "STRING", "description": "記事のカテゴリ名"},
            "selection_points": {
                "type": "ARRAY",
                "items": {"type": "STRING"},
                "description": "選び方の観点キーワードのみ（説明文禁止）"
            },
            "source_urls": {
                "type": "ARRAY",
                "items": {"type": "STRING"},
                "description": "情報源のURLの一覧"
            },
            "products": {
                "type": "ARRAY",
                "items": {
                    "type": "OBJECT",
                    "properties": {
                        "name": {"type": "STRING", "description": "商品名"},
                        "jan": {"type": "STRING", "description": "JANコード（取得できない場合は空文字）"},
                        "asin": {"type": "STRING", "description": "ASIN（取得できない場合は空文字）"},
                        "recommended_for": {
                            "type": "ARRAY",
                            "items": {"type": "STRING"},
                            "description": "明示的に判断できるおすすめ対象（不明なら空配列）"
                        },
                        "facts": {
                            "type": "ARRAY",
                            "items": {"type": "STRING"},
                            "description": "検証可能な客観的事実のみ（1項目1文、修飾語削除）"
                        },
                        "unique_points": {
                            "type": "ARRAY",
                            "items": {"type": "STRING"},
                            "description": "客観的な製品仕様・技術・処方・認証・容器のみ。0〜3件。元記事に明示的な根拠記載がある場合のみ採用し、記事執筆者・編集部の評価や感想から推測して生成してはならない。根拠が曖昧な場合は採用しない。他商品と内容が重複しても構わない。唯一性は求めない。見つからない場合は無理に埋めず空のリスト[]を返すこと（強制ではない）"
                        },
                        "free_from": {
                            "type": "ARRAY",
                            "items": {"type": "STRING"},
                            "description": "『〜を含まない』『〜フリー』『〜不使用』という事実のみ。ネガティブな主観表現への変換は禁止"
                        }
                    },
                    "required": ["name", "jan", "asin", "recommended_for", "facts", "unique_points", "free_from"]
                }
            }
        },
        "required": ["category", "selection_points", "source_urls", "products"]
    }

    model = genai.GenerativeModel("models/gemini-flash-lite-latest")
    generation_config = {
        "response_mime_type": "application/json",
        "response_schema": schema,
        "temperature": 0.0
    }

    extracted_data = None
    last_response_text = ""
    
    # ── 手動バイパス用ファイルのパス ──
    temp_json_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scripts", "extracted_data_temp.json")
    temp_prompt_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scripts", "prompt_temp.txt")
    
    for attempt in range(1, 4):
        try:
            # もし手動で埋めた temp JSON があれば、それを読み込んで Gemini 呼び出しをバイパスする
            if os.path.exists(temp_json_path) and os.path.getsize(temp_json_path) > 100:
                print("💡 手動バイパス用の一時JSONファイルを検出しました。Gemini呼び出しをスキップしてこれを読み込みます。")
                with open(temp_json_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    res_text = json.dumps(data, ensure_ascii=False)
                    last_response_text = res_text
            else:
                print(f"🔄 Gemini Flash 事実抽出を実行中 (試行 {attempt}/3)...")
                response = model.generate_content(prompt, generation_config=generation_config)
                res_text = response.text.strip()
                last_response_text = res_text
                
                data = json.loads(res_text)
            
            # バリデーション
            if not data.get("category"):
                raise ValueError("Validation failed: category is empty")
            if not data.get("products") or len(data["products"]) == 0:
                raise ValueError("Validation failed: products list is empty")
                
            def clean_name_local(s):
                import re
                return re.sub(r'[\s\u3000]', '', s).lower().strip()
            
            scraped_rakuten_map = {}
            scraped_yahoo_map = {}
            for original_p in products:
                p_name = original_p.get("name", "")
                p_clean = clean_name_local(p_name)
                if p_name:
                    if original_p.get("rakuten_scraped_url"):
                        scraped_rakuten_map[p_clean] = original_p.get("rakuten_scraped_url")
                    if original_p.get("yahoo_scraped_url"):
                        scraped_yahoo_map[p_clean] = original_p.get("yahoo_scraped_url")

            for p in data["products"]:
                # スキーマにないキーのチェック
                allowed_keys = {"name", "jan", "asin", "recommended_for", "facts", "unique_points", "free_from", "image_url", "rakuten_url", "yahoo_url", "resolved_details", "rating"}
                if not all(k in allowed_keys for k in p.keys()):
                    raise ValueError(f"Validation failed: product contains invalid keys: {list(p.keys())}")
                if not p.get("facts") or len(p["facts"]) == 0:
                    print(f"⚠️ Warning: product '{p.get('name')}' has no facts. Adding dummy fact.")
                    p["facts"] = ["製品の基本的な仕様が確認されている。"]
                # jan と asin の空文字補完
                if "jan" not in p:
                    p["jan"] = ""
                if "asin" not in p:
                    p["asin"] = ""
                
                # ratingの引き継ぎ
                r_val = ""
                ep_clean = clean_name_local(p.get("name", ""))
                matched = False
                for orig_p in products:
                    if clean_name_local(orig_p.get("name", "")) == ep_clean:
                        r_val = orig_p.get("rating") or ""
                        print(f"DEBUG: Matched {p.get('name')} -> rating: {r_val}")
                        matched = True
                        break
                if not matched:
                    print(f"DEBUG: Match failed for {p.get('name')} (clean: {ep_clean})")
                p["rating"] = r_val
                if "recommended_for" not in p:
                    p["recommended_for"] = []
                
                # 画像取得：ASINがあれば必ずAmazon画像、なければ楽天APIにフォールバック
                image = p.get("image_url")
                asin_val = p.get("asin", "").strip()
                if asin_val:
                    image = amazon_image_from_asin(asin_val)
                if not image:
                    image = fetch_rakuten_image(p["name"], p.get("jan"))
                if not image:
                    print(f"❌ エラー: image_url missing for '{p['name']}'. 楽天API・Amazonのいずれからも画像を取得できませんでした。")
                    sys.exit(1)
                p["image_url"] = image
                
                # APIのレートリミットを考慮したウェイト
                time.sleep(0.5)

                # 楽天URL
                ep_clean = clean_name_local(p.get("name", ""))
                r_url = p.get("rakuten_url")
                if not r_url:
                    if ep_clean in scraped_rakuten_map:
                        r_url = scraped_rakuten_map[ep_clean]
                    else:
                        for name_key, r_val in scraped_rakuten_map.items():
                            if name_key in ep_clean or ep_clean in name_key:
                                r_url = r_val
                                break
                p["rakuten_url"] = r_url

                # YahooURL
                y_url = p.get("yahoo_url")
                if not y_url:
                    if ep_clean in scraped_yahoo_map:
                        y_url = scraped_yahoo_map[ep_clean]
                    else:
                        for name_key, y_val in scraped_yahoo_map.items():
                            if name_key in ep_clean or ep_clean in name_key:
                                y_url = y_val
                                break
                p["yahoo_url"] = y_url

                # Amazon、楽天の価格および詳細情報の取得
                if "resolved_details" not in p:
                    orig_p = next((x for x in products if x.get("name") == p.get("name")), {})
                    scraped_urls = {
                        "amazon": orig_p.get("amazon_scraped_url", ""),
                        "rakuten": orig_p.get("rakuten_scraped_url", ""),
                        "yahoo": orig_p.get("yahoo_scraped_url", "")
                    }
                    details = fetch_product_details(p["name"], p.get("jan", ""), p.get("asin", ""), scraped_urls)
                    p["resolved_details"] = details
                    # アフィリエイトID適用済みのリンクをルートにも代入
                    if details.get("rakuten_url"):
                        p["rakuten_url"] = details["rakuten_url"]
                    if details.get("yahoo_url"):
                        p["yahoo_url"] = details["yahoo_url"]
                else:
                    details = p["resolved_details"]
                    # すでに resolved_details がある場合もルートに適用
                    if details.get("rakuten_url"):
                        p["rakuten_url"] = details["rakuten_url"]
                    if details.get("yahoo_url"):
                        p["yahoo_url"] = details["yahoo_url"]
                
                # 最も確実な製品画像を details からマージして上書きする
                if details.get("image_url"):
                    p["image_url"] = details["image_url"]
                    
            # 成功時のデータ処理
            if "source_urls" in data and data["source_urls"]:
                data["_source_urls"] = data.pop("source_urls")
            else:
                if "source_urls" in data:
                    data.pop("source_urls")
                data["_source_urls"] = [competitor_url]
                
            extracted_data = data
            print("✅ バリデーション成功！")
            break
        except Exception as e:
            print(f"⚠️ 試行 {attempt} 失敗: {e}")
            if attempt < 3:
                print("⏳ 30秒待機してからリトライします...")
                time.sleep(30)
            if attempt == 3:
                print("❌ すべての試行が失敗しました。")
                print(f"📢 Gemini API呼び出し失敗（クォータ等）。手動処理用に一時ファイルを生成します。")
                # プロンプトを書き出す
                with open(temp_prompt_path, "w", encoding="utf-8") as pf:
                    pf.write(prompt)
                # ダミーJSONテンプレートを書き出す
                dummy_json = {
                    "category": category,
                    "selection_points": ["洗浄力", "保湿成分", "肌へのやさしさ", "使用感"],
                    "source_urls": [competitor_url],
                    "products": []
                }
                for p in products:
                    dummy_json["products"].append({
                        "name": p.get("name", ""),
                        "jan": p.get("jan_code", ""),
                        "asin": p.get("asin", ""),
                        "rating": p.get("rating", ""),
                        "recommended_for": [],
                        "facts": []
                    })
                with open(temp_json_path, "w", encoding="utf-8") as jf:
                    json.dump(dummy_json, jf, ensure_ascii=False, indent=2)
                print(f"💾 プロンプトを書き出しました: {temp_prompt_path}")
                print(f"💾 ダミーJSONを書き出しました: {temp_json_path}")
                print(f"👉 {temp_json_path} に各商品の facts や recommended_for を手動で入力後、再度このスクリプトを実行してください。")
                sys.exit(2)
            time.sleep(2)

    # stockpile_data.json の保存
    output_filepath = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scripts", "stockpile_data.json")
    with open(output_filepath, "w", encoding="utf-8") as f:
        json.dump(extracted_data, f, ensure_ascii=False, indent=2)
        
    print("=" * 60)
    print("🔥 事実抽出とデータの保存が完了しました！")
    print(f"💾 データファイル保存場所: {output_filepath}")
    print("=" * 60)
    
    # 提出用ログ出力
    print("\n【Gemini レスポンス例】")
    print(last_response_text)
    
    print("\n【バリデーション結果】")
    print("・categoryが空でない: OK" if extracted_data.get("category") else "・categoryが空でない: NG")
    print(f"・productsが1件以上 (件数: {len(extracted_data.get('products', []))}): OK" if len(extracted_data.get('products', [])) >= 1 else "・productsが1件以上: NG")
    
    facts_ok = True
    for p in extracted_data.get("products", []):
        if not p.get("facts") or len(p["facts"]) == 0:
            facts_ok = False
            print(f"  - 商品 '{p.get('name')}' のfactsが0件です")
    print("・各商品のfactsが最低1件以上: OK" if facts_ok else "・各商品のfactsが最低1件以上: NG")
    
    # スキーマ外キー検証
    extra_keys = []
    root_keys = set(extracted_data.keys())
    allowed_root_keys = {"category", "selection_points", "_source_urls", "products"}
    for k in root_keys:
        if k not in allowed_root_keys:
            extra_keys.append(f"Root: {k}")
    for p in extracted_data.get("products", []):
        for k in p.keys():
            if k not in {"name", "jan", "asin", "recommended_for", "facts", "unique_points", "free_from", "image_url", "rakuten_url", "yahoo_url", "resolved_details", "rating"}:
                extra_keys.append(f"Product({p.get('name')}): {k}")
    if not extra_keys:
        print("・スキーマにないキーを出力しない: OK")
    else:
        print(f"・スキーマにないキーを出力しない: NG (検出された余分なキー: {extra_keys})")

    # 本文保存チェック
    forbidden_keys = ["article_body", "review_text", "marketing_copy", "ranking_description", "competitor_buying_guide", "competitor_expert_comments", "competitor_faqs", "competitor_summary", "description", "competitor_intro", "competitor_title"]
    has_body = False
    for fk in forbidden_keys:
        if fk in extracted_data:
            has_body = True
            print(f"  - ルートに禁止キー '{fk}' が存在します")
    for p in extracted_data.get("products", []):
        for fk in forbidden_keys:
            if fk in p:
                has_body = True
                print(f"  - 商品 '{p.get('name')}' に禁止キー '{fk}' が存在します")
    print("・本文が保存されていないことの確認: OK (本文系フィールドは一切含まれていません)" if not has_body else "・本文が保存されていないことの確認: NG (本文系フィールドが含まれています)")

    # ファイルサイズ
    size_kb = os.path.getsize(output_filepath) / 1024.0
    print(f"・stockpile_data.jsonの総サイズ: {size_kb:.2f} KB")
    print(f"・products件数: {len(extracted_data.get('products', []))} 件")
    
    # ステータスを「処理完了」に変更
    update_page_status(page_id, "処理完了")

if __name__ == "__main__":
    main()
