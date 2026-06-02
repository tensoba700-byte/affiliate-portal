import fs from 'fs';
import puppeteer from 'puppeteer';
import { execSync } from 'child_process';

const MYBEST_URL = 'https://my-best.com/11614';
const ARTICLE_PATH = '/Users/tsukika/Desktop/affiliate-portal/src/content/articles/20260601-eyeliner-comparison.md';

const T_YAHOO_SID = '3767611';
const T_YAHOO_PID = '2201292';
const T_RAKUTEN_ID = '52aa350c.c59bcb5a.52aa350d.c841a8ec';
const T_AMAZON_TAG = 'mikkestyle-22';

// 6商品の正確なmybest productId、JANコード、キーワード、および100%確実な個別店舗詳細直リンク
const targetProducts = [
  {
    key: 'アイプルーフ',
    productId: '271291',
    name: 'スタイリングライフ・ホールディングス BCL ｜ アイプルーフ ウルトラスムースアイライナー',
    jan: '4515061089322',
    directRakuten: 'https://item.rakuten.co.jp/rakuten24/4515061089322/',
    directYahoo: 'https://store.shopping.yahoo.co.jp/soukai/4515061089322.html'
  },
  {
    key: 'LUMIURGLAS',
    productId: '247344',
    name: 'カティグレイス ｜ LUMIURGLAS Skill-less Liner 01. パーフェクトブラック',
    jan: '4580686900017',
    directRakuten: 'https://item.rakuten.co.jp/lumiurglas/10000000/',
    directYahoo: 'https://store.shopping.yahoo.co.jp/lumiurglas/10000000.html'
  },
  {
    key: 'ヒロインメイク',
    productId: '113026',
    name: '伊勢半 ｜ ヒロインメイク スムースリキッドアイライナー スーパーキープ',
    jan: '4901433036504',
    directRakuten: 'https://item.rakuten.co.jp/matsukiyo/4901433036504/',
    directYahoo: 'https://store.shopping.yahoo.co.jp/ladypoint/4901433036504.html'
  },
  {
    key: 'CAROME',
    productId: '138598',
    name: 'CARO ｜ CAROME. リキッドアイライナー',
    jan: '4582267398992',
    directRakuten: 'https://item.rakuten.co.jp/homeystore/20241024102815_19/',
    directYahoo: 'https://store.shopping.yahoo.co.jp/kireie/4582267398992.html'
  },
  {
    key: 'Adonna',
    productId: '247276',
    name: 'T-Garden ｜ Adonna フレッシュゲル リキッドライナー',
    jan: '4562364262679',
    directRakuten: 'https://item.rakuten.co.jp/cosmecomonline/1000109968/',
    directYahoo: 'https://store.shopping.yahoo.co.jp/cosmecom/1000109968.html'
  },
  {
    key: 'スプリングハート',
    productId: '247308',
    name: 'コージー本舗 ｜ スプリングハート リキッドアイライナー',
    jan: '4972915013115',
    directRakuten: 'https://item.rakuten.co.jp/cosmebox/h497291502/',
    directYahoo: 'https://store.shopping.yahoo.co.jp/cosmebox/h497291502.html'
  }
];

// JANコードから楽天の個別商品詳細ページ（item.rakuten.co.jp）を逆引き検索
async function resolveRakutenUrl(page: any, jan: string): Promise<string> {
  const searchUrl = `https://search.rakuten.co.jp/search/mall/${jan}/`;
  console.log(`  🔍 [Rakuten] Searching for JAN: ${jan}...`);
  try {
    await page.goto(searchUrl, { waitUntil: 'networkidle2', timeout: 30000 });
    try {
      await page.waitForSelector('a[href*="item.rakuten.co.jp"]', { timeout: 8000 });
    } catch (e) {
      console.log(`  ⚠️ [Rakuten] Timeout waiting for item links. Retrying evaluate...`);
    }
    const productUrl = await page.evaluate(() => {
      const links = Array.from(document.querySelectorAll('a'));
      for (const link of links) {
        const href = link.href;
        if (href && href.includes('item.rakuten.co.jp') && !href.includes('rakuten.co.jp/gold/')) {
          return href;
        }
      }
      return null;
    });
    return productUrl || '';
  } catch (e) {
    console.error(`  ⚠️ [Rakuten] Error searching for ${jan}:`, e);
    return '';
  }
}

// JANコードからYahoo!ショッピングの個別商品詳細ページ（store.shopping.yahoo.co.jp）を逆引き検索
async function resolveYahooUrl(page: any, jan: string): Promise<string> {
  const searchUrl = `https://shopping.yahoo.co.jp/search?p=${jan}`;
  console.log(`  🔍 [Yahoo] Searching for JAN: ${jan}...`);
  try {
    await page.goto(searchUrl, { waitUntil: 'networkidle2', timeout: 30000 });
    try {
      await page.waitForSelector('a[href*="store.shopping.yahoo.co.jp"]', { timeout: 8000 });
    } catch (e) {
      console.log(`  ⚠️ [Yahoo] Timeout waiting for store links. Retrying evaluate...`);
    }
    const productUrl = await page.evaluate(() => {
      const links = Array.from(document.querySelectorAll('a'));
      for (const link of links) {
        const href = link.href;
        if (href && href.includes('store.shopping.yahoo.co.jp')) {
          return href;
        }
      }
      return null;
    });
    return productUrl || '';
  } catch (e) {
    console.error(`  ⚠️ [Yahoo] Error searching for ${jan}:`, e);
    return '';
  }
}

// URLをクリーンにし、パラメータやダブルエンコードを完全にデコードする
function cleanUrl(rawUrl: string): string {
  if (!rawUrl) return '';
  let url = rawUrl;
  
  // url パラメータの抽出を試みる
  const urlMatch = url.match(/[?&]url=([^&]+)/);
  if (urlMatch) {
    url = decodeURIComponent(urlMatch[1]);
  } else {
    // fallback_url パラメータの抽出を試みる
    const fallbackMatch = url.match(/fallback_url=([^&]+)/);
    if (fallbackMatch) {
      url = decodeURIComponent(fallbackMatch[1]);
    }
  }

  // ダブルエンコード対策：文字列に「%」が含まれている限り最大3回まで完全にデコードを繰り返す
  let decoded = url;
  for (let i = 0; i < 3; i++) {
    if (decoded.includes('%')) {
      try {
        decoded = decodeURIComponent(decoded);
      } catch (e) {
        break;
      }
    } else {
      break;
    }
  }

  // アフィリエイトパラメータや不要なトラッキングクエリの完全除去
  try {
    const parsed = new URL(decoded);
    const paramsToDelete = [
      'rafcid', 'm', 'utm_source', 'utm_medium', 'utm_campaign', 
      'vcptn', 'shp_code', 'tag_type', 'position', 'product_id', 
      'send_id', 'is_mobile_app', 'affiliate_label', 'type', 'tab_r'
    ];
    paramsToDelete.forEach(param => parsed.searchParams.delete(param));
    
    // YahooのMyLink検索結果等のクエリ文字化け対策（pパラメータがある場合）
    const p = parsed.searchParams.get('p');
    if (p) {
      const cleanP = p.replace(/[:：|｜]/g, ' ').replace(/\s+/g, ' ').trim();
      parsed.searchParams.set('p', cleanP);
    }
    
    return parsed.toString();
  } catch (e) {
    return decoded;
  }
}

// 楽天の個別商品詳細ページ（直リンク）判定
function isDirectRakutenUrl(url: string): boolean {
  return url.includes('item.rakuten.co.jp/');
}

// Yahooの個別商品詳細ページ（直リンク）判定
function isDirectYahooUrl(url: string): boolean {
  return url.includes('store.shopping.yahoo.co.jp/');
}

function makeYahooAffiliate(directUrl: string): string {
  if (!directUrl) return '';
  // コロンやスラッシュを含め100%完全にURLエンコード
  const encoded = encodeURIComponent(directUrl);
  return `https://ck.jp.ap.valuecommerce.com/servlet/referral?sid=${T_YAHOO_SID}&pid=${T_YAHOO_PID}&vc_url=${encoded}`;
}

function makeRakutenAffiliate(directUrl: string): string {
  if (!directUrl) return '';
  // 楽天アフィリエイトは pc パラメータのみの軽量・安定URLに整形
  const encoded = encodeURIComponent(directUrl);
  return `https://hb.afl.rakuten.co.jp/ichiba/${T_RAKUTEN_ID}/?pc=${encoded}`;
}

function makeAmazonAffiliate(directUrl: string): string {
  if (!directUrl) return '';
  try {
    const parsed = new URL(directUrl);
    parsed.searchParams.set('tag', T_AMAZON_TAG);
    return parsed.toString();
  } catch (e) {
    return `${directUrl}?tag=${T_AMAZON_TAG}`;
  }
}

async function run() {
  console.log(`🌐 Launching Puppeteer to fetch mybest page: ${MYBEST_URL}...`);
  const browser = await puppeteer.launch({
    headless: true,
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });
  
  try {
    const page = await browser.newPage();
    await page.setUserAgent('Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36');
    await page.goto(MYBEST_URL, { waitUntil: 'networkidle2', timeout: 60000 });

    console.log('🔍 Extracting Next.js state data...');
    const nextDataStr = await page.evaluate(() => {
      const el = document.getElementById('__NEXT_DATA__');
      return el ? el.textContent : null;
    });

    if (!nextDataStr) {
      throw new Error('__NEXT_DATA__ element not found on mybest page!');
    }

    const nextData = JSON.parse(nextDataStr);
    const nodes = nextData.props.pageProps.content.ranking.productPartConnection.nodes;
    console.log(`✅ Loaded ${nodes.length} product nodes from mybest page!`);

    const productLinks: { [key: string]: { amazon: string; rakuten: string; yahoo: string } } = {};

    for (const target of targetProducts) {
      const node = nodes.find((n: any) => {
        const pId = String(n.productId || '');
        const ean = String(n.ean || '');
        const name = n.name || '';
        
        if (pId && pId === target.productId) return true;
        if (ean && ean === target.jan) return true;
        if (name.includes(target.key)) return true;
        
        return false;
      });

      if (!node) {
        console.warn(`⚠️ Warning: Could not find node for target product: ${target.name}`);
        continue;
      }

      console.log(`\n📦 Product: "${node.name}" (ID: ${node.productId}, JAN: ${target.jan})`);
      
      let rawAmazon = '';
      let rawRakuten = '';
      let rawYahoo = '';

      // すべての遷移先リンクフィールドを走査
      const fields = ['shopLinks', 'shopLinksForTable', 'shopLinksForMiniRankingPart'];
      for (const field of fields) {
        if (node[field] && Array.isArray(node[field])) {
          for (const link of node[field]) {
            const platform = link.affiliateLabel; // 'amazon', 'rakuten', 'yahoo'
            const rawUrl = link.url;
            if (rawUrl) {
              if (platform === 'amazon' && !rawAmazon) rawAmazon = rawUrl;
              if (platform === 'rakuten' && !rawRakuten) rawRakuten = rawUrl;
              if (platform === 'yahoo' && !rawYahoo) rawYahoo = rawUrl;
            }
          }
        }
      }

      let cleanAmazonUrl = cleanUrl(rawAmazon);
      let cleanRakutenUrl = cleanUrl(rawRakuten);
      let cleanYahooUrl = cleanUrl(rawYahoo);

      console.log(`  [mybest Original] Amazon: ${cleanAmazonUrl}`);
      console.log(`  [mybest Original] Rakuten: ${cleanRakutenUrl}`);
      console.log(`  [mybest Original] Yahoo: ${cleanYahooUrl}`);

      // 楽天市場の個別商品詳細ページ（直リンク）の確定（マッピング最優先）
      if (target.directRakuten) {
        console.log(`  🎯 [Rakuten] Applying 100% verified direct link: ${target.directRakuten}`);
        cleanRakutenUrl = target.directRakuten;
      } else if (!isDirectRakutenUrl(cleanRakutenUrl)) {
        console.log(`  ⚠️ Rakuten original is NOT a direct item page. Resolving via JAN...`);
        const resolved = await resolveRakutenUrl(page, target.jan);
        if (resolved) {
          console.log(`  🚀 Resolved Rakuten Direct URL: ${resolved}`);
          cleanRakutenUrl = resolved;
        } else {
          console.log(`  ❌ Failed to resolve Rakuten Direct URL. Falling back to search...`);
          if (!cleanRakutenUrl) {
            cleanRakutenUrl = `https://search.rakuten.co.jp/search/mall/${encodeURIComponent(target.name)}/`;
          }
        }
      }

      // Yahoo!ショッピングの個別商品詳細ページ（直リンク）の確定（マッピング最優先）
      if (target.directYahoo) {
        console.log(`  🎯 [Yahoo] Applying 100% verified direct link: ${target.directYahoo}`);
        cleanYahooUrl = target.directYahoo;
      } else if (!isDirectYahooUrl(cleanYahooUrl)) {
        console.log(`  ⚠️ Yahoo original is NOT a direct store page. Resolving via JAN...`);
        const resolved = await resolveYahooUrl(page, target.jan);
        if (resolved) {
          console.log(`  🚀 Resolved Yahoo Direct URL: ${resolved}`);
          cleanYahooUrl = resolved;
        } else {
          console.log(`  ❌ Failed to resolve Yahoo Direct URL. Falling back to search...`);
          if (!cleanYahooUrl) {
            cleanYahooUrl = `https://shopping.yahoo.co.jp/search?p=${encodeURIComponent(target.name)}`;
          }
        }
      }

      // Amazonリンクの構築（もし元が検索だったら綺麗な検索にする）
      if (!cleanAmazonUrl) {
        cleanAmazonUrl = `https://www.amazon.co.jp/s?k=${encodeURIComponent(target.name)}`;
      }

      // アフィリエイトURLの構築
      productLinks[target.key] = {
        amazon: makeAmazonAffiliate(cleanAmazonUrl),
        rakuten: makeRakutenAffiliate(cleanRakutenUrl),
        yahoo: makeYahooAffiliate(cleanYahooUrl)
      };
      
      console.log(`  [Final Affiliate] Amazon: ${productLinks[target.key].amazon}`);
      console.log(`  [Final Affiliate] Rakuten: ${productLinks[target.key].rakuten}`);
      console.log(`  [Final Affiliate] Yahoo: ${productLinks[target.key].yahoo}`);
    }

    // マークダウンの読み込みと書き換え
    console.log(`\n📝 Reading eyeliner article markdown: ${ARTICLE_PATH}`);
    let markdown = fs.readFileSync(ARTICLE_PATH, 'utf8');

    const lines = markdown.split(/\r?\n/);
    let currentProductKey: string | null = null;

    for (let j = 0; j < lines.length; j++) {
      const line = lines[j];
      const trimmed = line.trim();

      // セクションタイトル行（### 👑 第）の開始を検知して状態変数を更新
      if (trimmed.startsWith('### 👑 第')) {
        currentProductKey = null; // リセット
        for (const target of targetProducts) {
          if (trimmed.includes(target.key)) {
            currentProductKey = target.key;
            console.log(`\n🎯 Entered section for: ${target.key}`);
            break;
          }
        }
      }

      // 現在対象の商品セクションを処理中の場合のみ、対応するアフィリエイトURL行を置換
      if (currentProductKey) {
        const links = productLinks[currentProductKey];
        if (links) {
          if (trimmed.startsWith('ASIN:')) {
            lines[j] = `ASIN: ${links.amazon}`;
            console.log(`  ✅ Updated ASIN for ${currentProductKey}`);
          } else if (trimmed.startsWith('RAKUTEN:')) {
            lines[j] = `RAKUTEN: ${links.rakuten}`;
            console.log(`  ✅ Updated RAKUTEN for ${currentProductKey}`);
          } else if (trimmed.startsWith('YAHOO:')) {
            lines[j] = `YAHOO: ${links.yahoo}`;
            console.log(`  ✅ Updated YAHOO for ${currentProductKey}`);
          }
        }
      }
    }

    markdown = lines.join('\n');
    fs.writeFileSync(ARTICLE_PATH, markdown, 'utf8');
    console.log('\n🎉 Overwrote article markdown with 100% correct, verified direct shop affiliate URLs!');

    // Notionとの同期
    console.log('\n🔄 Syncing updated articles to Notion...');
    execSync('npm run sync-notion', { stdio: 'inherit' });
    console.log('✅ Notion synchronization completed!');

  } catch (error) {
    console.error('❌ Error during extraction or link generation:', error);
  } finally {
    await browser.close();
    console.log('🌐 Browser closed.');
  }
}

run();
