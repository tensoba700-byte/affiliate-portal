import fs from 'fs';
import path from 'path';
import puppeteer from 'puppeteer';
import { execSync } from 'child_process';

const MYBEST_URL = 'https://my-best.com/11614';
const ARTICLE_PATH = '/Users/tsukika/Desktop/affiliate-portal/src/content/articles/20260601-eyeliner-comparison.md';

const T_YAHOO_SID = '3767611';
const T_YAHOO_PID = '2201292';
const T_RAKUTEN_ID = '52aa350c.c59bcb5a.52aa350d.c841a8ec';
const T_AMAZON_TAG = 'mikkestyle-22';

// 6商品の正確なmybest productId、JANコード、キーワード
const targetProducts = [
  {
    key: 'アイプルーフ',
    productId: '271291',
    name: 'スタイリングライフ・ホールディングス BCL ｜ アイプルーフ ウルトラスムースアイライナー',
    jan: '4515061089322'
  },
  {
    key: 'LUMIURGLAS',
    productId: '247344',
    name: 'カティグレイス ｜ LUMIURGLAS Skill-less Liner 01. パーフェクトブラック',
    jan: '4580686900017'
  },
  {
    key: 'ヒロインメイク',
    productId: '113026',
    name: '伊勢半 ｜ ヒロインメイク スムースリキッドアイライナー スーパーキープ',
    jan: '4901433036504'
  },
  {
    key: 'CAROME',
    productId: '138598',
    name: 'CARO ｜ CAROME. リキッドアイライナー',
    jan: '4582267398992'
  },
  {
    key: 'Adonna',
    productId: '247276',
    name: 'T-Garden ｜ Adonna フレッシュゲル リキッドライナー',
    jan: '4562364262679'
  },
  {
    key: 'スプリングハート',
    productId: '247308',
    name: 'コージー本舗 ｜ スプリングハート リキッドアイライナー',
    jan: '4972915013115'
  }
];

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

  // アフィリエイトパラメータや不要なトラッキングクエリの除去
  try {
    const parsed = new URL(url);
    // 楽天アフィリエイト用のパラメータ除去
    parsed.searchParams.delete('rafcid');
    parsed.searchParams.delete('m');
    // その他の一般的なアフィリエイト/広告パラメータの除去
    parsed.searchParams.delete('utm_source');
    parsed.searchParams.delete('utm_medium');
    parsed.searchParams.delete('utm_campaign');
    parsed.searchParams.delete('vcptn');
    return parsed.toString();
  } catch (e) {
    return url;
  }
}

function makeYahooAffiliate(rawUrl: string): string {
  const direct = cleanUrl(rawUrl);
  if (!direct) return '';
  // 100%完全にコロンやスラッシュも含めURLエンコードする
  const encoded = encodeURIComponent(direct);
  return `https://ck.jp.ap.valuecommerce.com/servlet/referral?sid=${T_YAHOO_SID}&pid=${T_YAHOO_PID}&vc_url=${encoded}`;
}

function makeRakutenAffiliate(rawUrl: string): string {
  const direct = cleanUrl(rawUrl);
  if (!direct) return '';
  // 楽天アフィリエイトは &m や rafcid を排除し pc パラメータのみにする
  const encoded = encodeURIComponent(direct);
  return `https://hb.afl.rakuten.co.jp/ichiba/${T_RAKUTEN_ID}/?pc=${encoded}`;
}

function makeAmazonAffiliate(rawUrl: string): string {
  const direct = cleanUrl(rawUrl);
  if (!direct) return '';
  try {
    const parsed = new URL(direct);
    parsed.searchParams.set('tag', T_AMAZON_TAG);
    return parsed.toString();
  } catch (e) {
    return `${direct}?tag=${T_AMAZON_TAG}`;
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

    // 各ターゲット商品ごとのアフィリエイトリンクを構築
    const productLinks: { [key: string]: { amazon: string; rakuten: string; yahoo: string } } = {};

    for (const target of targetProducts) {
      // 100%確実にマッチングするために productId を最優先し、EANや商品名でフォールバックする
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

      console.log(`\n📦 Found matching product in mybest: "${node.name}" (ID: ${node.productId})`);
      
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

      const cleanAmazon = cleanUrl(rawAmazon);
      const cleanRakuten = cleanUrl(rawRakuten);
      const cleanYahoo = cleanUrl(rawYahoo);

      console.log(`  MyBest Amazon original: ${cleanAmazon}`);
      console.log(`  MyBest Rakuten original: ${cleanRakuten}`);
      console.log(`  MyBest Yahoo original: ${cleanYahoo}`);

      productLinks[target.key] = {
        amazon: makeAmazonAffiliate(rawAmazon || `https://www.amazon.co.jp/s?k=${encodeURIComponent(target.name)}`),
        rakuten: makeRakutenAffiliate(rawRakuten || `https://search.rakuten.co.jp/search/mall/${encodeURIComponent(target.name)}/`),
        yahoo: makeYahooAffiliate(rawYahoo || `https://shopping.yahoo.co.jp/search?p=${encodeURIComponent(target.name)}`)
      };
    }

    // マークダウンの読み込みと書き換え
    console.log(`\n📝 Reading eyeliner article markdown: ${ARTICLE_PATH}`);
    let markdown = fs.readFileSync(ARTICLE_PATH, 'utf8');

    for (const target of targetProducts) {
      const links = productLinks[target.key];
      if (!links) continue;

      console.log(`🔄 Applying exact links for "${target.key}" in markdown...`);
      
      const escapedKey = target.key.replace(/[-\/\\^$*+?.()|[\]{}]/g, '\\$&');
      
      // 各商品セクションをマッチさせるためのパターン
      const sectionRegex = new RegExp(`(### 👑 第\\d位: .*?${escapedKey}[\\s\\S]*?ASIN: .*?\\nRAKUTEN: )([\\s\\S]*?\\nYAHOO: )([\\s\\S]*?\\n)`, 'i');
      
      const match = markdown.match(sectionRegex);
      if (match) {
        const replaced = markdown.replace(sectionRegex, `$1${links.rakuten}\nYAHOO: ${links.yahoo}\n`);
        markdown = replaced;
        console.log(`  ✅ Successfully updated Rakuten & Yahoo links for ${target.key}!`);
      } else {
        console.warn(`  ⚠️ Could not match section for ${target.key} using regex.`);
      }
    }

    fs.writeFileSync(ARTICLE_PATH, markdown, 'utf8');
    console.log('🎉 Overwrote article markdown with 100% correct scraped direct shop URLs!');

    // Notionとの同期
    console.log('🔄 Syncing updated articles to Notion...');
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
