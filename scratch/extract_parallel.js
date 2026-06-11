const puppeteer = require('puppeteer');
const fs = require('fs');
const path = require('path');

const targets = {
  "All About": {
    url: "https://allabout.co.jp/gm/gc/487779/",
    selector: '[itemprop="articleBody"], article',
    exclude: '.gm-related-article, .gm-ad, .ad, iframe, script, style, .guide-profile, .ranking-box'
  },
  "MAQUIA": {
    url: "https://maquia.hpplus.jp/skincare/article/117972/",
    selector: 'article, .article-body',
    exclude: '.article-related, .article-tag, .ad, iframe, script, style, .js-article-recommend, .article-author'
  },
  "Biteki": {
    url: "https://www.biteki.com/skin-care/trouble/760560",
    selector: 'article, .article-body-wrapper',
    exclude: '.related-post, .ad, iframe, script, style, .recommended-articles, .ranking-box, .article-footer'
  },
  "MERY": {
    url: "https://mery.jp/2464749",
    selector: 'article, .mery-article-body',
    exclude: '.mery-ad, .ad, iframe, script, style, .related-articles, .recommend-links, .writer-profile'
  },
  "michill": {
    url: "https://michill.jp/author/column/133036",
    selector: '.column-detail__body, article',
    exclude: '.related-link, .ad, iframe, script, style, .recommend-box, .writer-info'
  },
  "my-best": {
    url: "https://my-best.com/461",
    selector: 'article, .sg-entry-content',
    exclude: '.related-ranking, .ad, iframe, script, style, .buying-guide-recommend, .buying-guide-related, .author-profile'
  }
};

async function extractSite(browser, name, config) {
  const page = await browser.newPage();
  await page.setUserAgent('Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/120.0.0.0');
  
  // 不要アセットのブロック
  await page.setRequestInterception(true);
  page.on('request', (req) => {
    if (['image', 'font', 'media'].includes(req.resourceType())) {
      req.abort();
    } else {
      req.continue();
    }
  });

  const url = config.url;
  const filePath = path.join(__dirname, `extract_test_${name.toLowerCase().replace(/\s+/g, '_')}.txt`);

  try {
    // domcontentloaded で高速読み込み
    await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 35000 });
    await new Promise(r => setTimeout(r, 1000));
    await page.waitForSelector(config.selector, { timeout: 15000 });

    const extraction = await page.evaluate((sel, excludeSel) => {
      const title = document.querySelector('h1')?.textContent.trim() || document.title || "";
      const mainEl = document.querySelector(sel);
      
      if (!mainEl) {
        return { title, content: "ERROR: Content element not found with selector: " + sel };
      }

      const clone = mainEl.cloneNode(true);
      if (excludeSel) {
        const excludes = clone.querySelectorAll(excludeSel);
        excludes.forEach(el => el.remove());
      }

      const blocks = [];
      const walker = document.createTreeWalker(clone, NodeFilter.SHOW_ELEMENT, {
        acceptNode: function(node) {
          const tagName = node.tagName.toLowerCase();
          if (['h1', 'h2', 'h3', 'h4', 'h5', 'p', 'li'].includes(tagName)) {
            return NodeFilter.FILTER_ACCEPT;
          }
          return NodeFilter.FILTER_SKIP;
        }
      });

      let currentNode;
      while (currentNode = walker.nextNode()) {
        const tag = currentNode.tagName.toLowerCase();
        const text = currentNode.textContent.trim();
        
        if (text.length > 3) {
          const skipKeywords = ["広告", "関連記事", "あわせて読みたい", "おすすめ記事", "ライタープロフィール", "前へ", "次へ", "一覧に戻る", "会員登録", "ログイン"];
          if (skipKeywords.some(kw => text.includes(kw))) {
            continue;
          }
          if (tag.startsWith('h')) {
            blocks.push(`\n[${tag.toUpperCase()}] ${text}\n`);
          } else {
            blocks.push(text);
          }
        }
      }

      return { title, content: blocks.join('\n\n') };
    }, config.selector, config.exclude);

    fs.writeFileSync(filePath, `URL: ${url}\nTITLE: ${extraction.title}\n\n${extraction.content}`, 'utf8');
    
    // 機械チェック：テキスト破損バグ
    const hasOf = extraction.content.includes(" of ") || extraction.title.includes(" of ");
    const hasKudasai = extraction.content.includes("ください") || extraction.title.includes("ください");
    
    // 「くすみ」の箇所の特定
    const matchesKusumi = extraction.content.match(/くすみ|ください/g);

    console.log(`[SUCCESS] ${name} | Chars: ${extraction.content.length} | File: ${filePath}`);
    console.log(`  - title: "${extraction.title}"`);
    console.log(`  - " of " detected: ${hasOf}`);
    console.log(`  - "ください" detected: ${hasKudasai}`);
    if (hasKudasai) {
      // くださいを含む段落をダンプ
      const paragraphs = extraction.content.split('\n');
      const targetP = paragraphs.filter(p => p.includes("ください"));
      console.log(`  - "ください" Context: "${targetP.join(' | ')}"`);
    }

    return { name, success: true, charCount: extraction.content.length, title: extraction.title, hasOf, hasKudasai };
  } catch (e) {
    console.log(`[FAILED] ${name} | Error: ${e.message}`);
    return { name, success: false, error: e.message };
  } finally {
    await page.close();
  }
}

async function run() {
  const browser = await puppeteer.launch({
    headless: true,
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });

  const promises = Object.entries(targets).map(([name, config]) => extractSite(browser, name, config));
  const results = await Promise.all(promises);

  console.log("\n=== Parallel Extraction Summary ===");
  console.log(JSON.stringify(results, null, 2));

  await browser.close();
  process.exit(0);
}

run().catch(console.error);
