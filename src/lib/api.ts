import fs from 'fs';
import path from 'path';
import matter from 'gray-matter';
import { remark } from 'remark';
import html from 'remark-html';
import remarkGfm from 'remark-gfm';

import type { Document } from '@contentful/rich-text-types';
import { contentfulClient } from '@/src/lib/contentful';

import type { Product } from '@/src/components/RankingTable';
import { SimpleCache } from './cache';
import { amazonUrl, amazonSearchUrl, rakutenUrl } from './affiliateHelpers';

// Cache for Yahoo Shopping results (TTL: 1 hour)
const yahooCache = new SimpleCache<{ price: string; url: string }>();
// Cache for Unsplash image results (TTL: 24 hours)
const imageCache = new SimpleCache<string>();

// Directory containing markdown articles (fallback)
const articlesDirectory = path.join(process.cwd(), 'src/content/articles');

/**
 * Article data structure used throughout the app.
 * Supports both Contentful rich‑text (`body`) and markdown fallback (`content`).
 */
export interface ArticleItem {
  id: string;
  title: string;
  slug: string;
  category?: string;
  excerpt?: string;
  thumbnail?: string | null;
  publishedAt?: string; // ISO string
  body?: Document; // Contentful rich‑text document
  coverImage?: string | null; // kept for markdown fallback
  content?: string; // rendered HTML from markdown fallback
  rankings: Product[]; // parsed product ranking data
}

/**
 * Fetch product data from Yahoo! Shopping API v3
 */
async function fetchYahooProduct(query: string): Promise<{ price: string; url: string } | null> {
  const cached = yahooCache.get(query);
  if (cached) return cached;

  const appid = process.env.YAHOO_SHOPPING_APP_ID;
  if (!appid) return null;

  try {
    const res = await fetch(
      `https://shopping.yahooapis.jp/ShoppingWebService/V3/itemSearch?appid=${appid}&query=${encodeURIComponent(query)}&results=1`
    );
    const data = await res.json();
    const hit = data.hits?.[0];

    if (hit) {
      const result = {
        price: `¥${hit.price.toLocaleString()}`,
        url: hit.url,
      };
      yahooCache.set(query, result);
      return result;
    }
  } catch (err) {
    console.error(`Yahoo API error for "${query}":`, err);
  }
  return null;
}

/**
 * Fetch a high-quality product image from Unsplash API
 */
async function fetchUnsplashImage(query: string): Promise<string | null> {
  const cached = imageCache.get(query);
  if (cached) return cached;

  const accessKey = process.env.UNSPLASH_ACCESS_KEY;
  if (!accessKey) return null;

  try {
    const res = await fetch(
      `https://api.unsplash.com/search/photos?query=${encodeURIComponent(query)}&per_page=1&client_id=${accessKey}`
    );
    const data = await res.json();
    const url = data.results?.[0]?.urls?.small;

    if (url) {
      imageCache.set(query, url);
      return url;
    }
  } catch (err) {
    console.error(`Unsplash API error for "${query}":`, err);
  }
  return null;
}

/**
 * Parse ranking sections from raw markdown content.
 * Looks for headings like "### 👑 第1位: 商品名" and rating tags like "[総合評価: 4.5]".
 */
export function parseRankingsFromMarkdown(raw: string): Product[] {
  const products: Product[] = [];
  const sections = raw.split(/(?=###[^\n]*第\d+位)/);
  for (const section of sections) {
    const rankMatch = section.match(/第(\d+)位[：:]\s*(.+)/);
    if (!rankMatch) continue;
    const rank = parseInt(rankMatch[1], 10);
    if (rank > 7) continue; // allow up to 7
    const name = rankMatch[2].replace(/\*\*/g, '').trim();
    const ratingMatch = section.match(/\[(?:RATING|総合評価)[：:]\s*([0-9.]+)\]/);
    const score = ratingMatch ? parseFloat(ratingMatch[1]) : 4.0;
    const q = encodeURIComponent(name);
    const product: Product = {
      rank,
      brand: '',
      name,
      imageUrl: '',
      score,
      amazon: { price: '価格を見る', url: `https://www.amazon.co.jp/s?k=${q}` },
      yahoo: { price: '価格を見る', url: `https://shopping.yahoo.co.jp/search?p=${q}` },
      rakuten: { price: '価格を見る', url: `https://search.rakuten.co.jp/search/mall/${q}/` },
      pros: [],
      cons: [],
      description: '',
      features: []
    };

    // Image URL from IMAGE: tag
    const imageMatch = section.match(/IMAGE:\s*(https?:\/\/[^\s]+)/i);
    if (imageMatch) product.imageUrl = imageMatch[1];

    // Amazon affiliate URL: ASIN: can be a full URL or bare ASIN code
    const amzMatch = section.match(/ASIN:\s*(https?:\/\/\S+|[A-Z0-9]{10})/i);
    if (amzMatch) {
      product.amazon = { price: '価格を見る', url: amazonUrl(amzMatch[1]) };
    }

    // Rakuten affiliate URL
    const rakutenMatch = section.match(/RAKUTEN:\s*(https?:\/\/[^\s]+)/i);
    if (rakutenMatch) {
      // Keep any URL-encoded pc= parameter as is
      const rawUrl = rakutenMatch[1];
      product.rakuten = { price: '価格を見る', url: rawUrl };
    }

    // Yahoo affiliate URL
    const yahooMatch = section.match(/YAHOO:\s*(https?:\/\/[^\s]+)/i);
    if (yahooMatch) {
      product.yahoo = { price: '価格を見る', url: yahooMatch[1] };
    }

    // Prices
    const amzPrice = section.match(/AMAZON_PRICE:\s*(\d+)/i);
    const rakPrice = section.match(/RAKUTEN_PRICE:\s*(\d+)/i);
    const yahPrice = section.match(/YAHOO_PRICE:\s*(\d+)/i);
    if (amzPrice && product.amazon) product.amazon.price = `${Number(amzPrice[1]).toLocaleString()}円`;
    if (rakPrice && product.rakuten) product.rakuten.price = `${Number(rakPrice[1]).toLocaleString()}円`;
    if (yahPrice && product.yahoo) product.yahoo.price = `${Number(yahPrice[1]).toLocaleString()}円`;

    // Parse Pros (advantages)
    const prosMatch = section.match(/:::pro\s*([\s\S]*?)\s*:::/);
    if (prosMatch) {
      product.pros = prosMatch[1]
        .split('\n')
        .map(line => line.replace(/^-\s*/, '').replace(/^\s*[\*•\+]\s*/, '').trim())
        .filter(line => line.length > 0);
    }

    // Parse Cons (disadvantages)
    const consMatch = section.match(/:::con\s*([\s\S]*?)\s*:::/);
    if (consMatch) {
      product.cons = consMatch[1]
        .split('\n')
        .map(line => line.replace(/^-\s*/, '').replace(/^\s*[\*•\+]\s*/, '').trim())
        .filter(line => line.length > 0);
    }

    // Parse Description (first standard paragraph)
    const bodyLines = section.split('\n').map(l => l.trim()).filter(l => l.length > 0);
    const descLine = bodyLines.find(line => 
      !line.startsWith('###') && 
      !line.startsWith('[') && 
      !line.startsWith('IMAGE:') && 
      !line.startsWith('AMAZON_PRICE:') && 
      !line.startsWith('RAKUTEN_PRICE:') && 
      !line.startsWith('YAHOO_PRICE:') && 
      !line.startsWith('ASIN:') && 
      !line.startsWith('RAKUTEN:') && 
      !line.startsWith('YAHOO:') &&
      !line.startsWith(':::') &&
      !line.startsWith('🔍') &&
      !line.startsWith('✍️') &&
      !line.startsWith('👤') &&
      !line.startsWith('-')
    );
    if (descLine) {
      const cleaned = descLine.replace(/\*\*/g, '').replace(/__/g, '').trim();
      product.description = cleaned.length > 120 ? cleaned.substring(0, 120) + '...' : cleaned;
    }

    // Extract dynamic feature tags based on keywords
    // Extract dynamic feature tags based on keywords or explicit FEATURES tag
    const features: string[] = [];
    const customFeaturesMatch = section.match(/FEATURES:\s*(.+)/i);
    if (customFeaturesMatch) {
      product.features = customFeaturesMatch[1].split(',').map(f => f.trim()).slice(0, 3);
    } else {
      const lowerContent = section.toLowerCase();
      if (lowerContent.includes('タイマー')) features.push('⏰ タイマー付き');
      if (lowerContent.includes('調光') || lowerContent.includes('明るさ調整')) features.push('💡 調光可能');
      if (lowerContent.includes('防水') || lowerContent.includes('防滴') || lowerContent.includes('防塵')) features.push('🛡️ 防水仕様');
      if (lowerContent.includes('静音') || lowerContent.includes('静か')) features.push('🔇 静音設計');
      if (lowerContent.includes('軽量') || lowerContent.includes('軽い') || lowerContent.includes('コンパクト')) features.push('🍃 軽量・小型');
      if (lowerContent.includes('高コスパ') || lowerContent.includes('リーズナブル') || lowerContent.includes('コスパ')) features.push('💎 高コスパ');
      if (lowerContent.includes('コードレス') || lowerContent.includes('充電式') || lowerContent.includes('バッテリー')) features.push('🔋 充電式');
      if (lowerContent.includes('2way') || lowerContent.includes('2ウェイ')) features.push('🔄 2WAY方式');
      
      if (features.length > 0) {
        product.features = features.slice(0, 3);
      }
    }

    products.push(product);
  }
  return products.sort((a, b) => a.rank - b.rank);
}

/** Fetch all articles, preferring Contentful and falling back to local markdown files. */
export async function getAllArticles(): Promise<ArticleItem[]> {
  // 1️⃣ Fetch local markdown files first
  let markdownArticles: ArticleItem[] = [];
  if (fs.existsSync(articlesDirectory)) {
    const fileNames = fs.readdirSync(articlesDirectory);
    const now = new Date();
    markdownArticles = fileNames
      .filter((fn) => fn.endsWith('.md') && fn !== 'GENERATION_RULES.md')
      .map((fn) => {
        const slug = fn.replace(/\.md$/, '').normalize('NFC');
        const fullPath = path.join(articlesDirectory, fn);
        const fileContents = fs.readFileSync(fullPath, 'utf8');
        const matterResult = matter(fileContents);

        // Priority: eyecatch PNG > frontmatter coverImage > first IMAGE: tag
        let coverImage: string | null = null;
        const eyecatchPngPath = path.join(process.cwd(), 'public', 'eyecatch', `${slug}.png`);
        if (fs.existsSync(eyecatchPngPath)) {
          coverImage = `/eyecatch/${slug}.png`;
        } else if (matterResult.data.coverImage) {
          coverImage = matterResult.data.coverImage;
        } else {
          const firstImageMatch = matterResult.content.match(/IMAGE:\s*(https?:\/\/[^\s]+)/i);
          if (firstImageMatch) coverImage = firstImageMatch[1];
        }

        return {
          id: slug,
          slug,
          title: matterResult.data.title || slug,
          coverImage,
          excerpt: matterResult.data.excerpt || '',
          publishedAt: matterResult.data.publishDate || now.toISOString(),
          content: matterResult.content,
          rankings: [],
          thumbnail: coverImage,
          category: matterResult.data.category || '',
          body: undefined,
        } as ArticleItem;
      })
      .sort((a, b) => {
        if (a.publishedAt && b.publishedAt) {
          return a.publishedAt < b.publishedAt ? 1 : -1;
        }
        return 0;
      });
  }

  // 2️⃣ Try Contentful as fallback/addition
  let cfArticles: ArticleItem[] = [];
  try {
    const entries = await contentfulClient.getEntries({
      content_type: 'Article',
      limit: 1000,
    });
    cfArticles = entries.items.map((item: any) => {
      const f = item.fields as any;
      return {
        id: item.sys.id,
        title: f.title ?? '',
        slug: f.slug ?? '',
        category: f.category ?? '',
        excerpt: f.excerpt ?? '',
        thumbnail: f.thumbnail?.fields?.file?.url ?? null,
        publishedAt: f.publishedAt ?? '',
        body: f.body as Document,
        coverImage: f.thumbnail?.fields?.file?.url ?? null,
        rankings: [],
      } as ArticleItem;
    });
  } catch (err) {
    console.error('Contentful fetch error (all):', err);
  }

  // Combine both, prioritizing Markdown
  const allArticles = [...markdownArticles];
  for (const cf of cfArticles) {
    if (!allArticles.some(a => a.slug === cf.slug)) {
      allArticles.push(cf);
    }
  }

  // JST時間基準での予約投稿判定（朝 07:00 / 夜 19:00 等の精密制御）
  const now = new Date();
  const publishedArticles = allArticles.filter(a => {
    if (!a.publishedAt) return true;
    try {
      let pubStr = String(a.publishedAt).trim();
      
      // YYYY-MM-DD 形式なら、デフォルトで朝 07:00 JST とする
      if (/^\d{4}-\d{2}-\d{2}$/.test(pubStr)) {
        pubStr = `${pubStr}T07:00:00+09:00`;
      }
      // YYYY-MM-DD HH:mm 形式なら JST 指定に変換
      else if (/^\d{4}-\d{2}-\d{2}\s\d{2}:\d{2}$/.test(pubStr)) {
        pubStr = `${pubStr.replace(' ', 'T')}:00+09:00`;
      }
      // YYYY-MM-DD HH:mm:ss 形式なら JST 指定に変換
      else if (/^\d{4}-\d{2}-\d{2}\s\d{2}:\d{2}:\d{2}$/.test(pubStr)) {
        pubStr = `${pubStr.replace(' ', 'T')}+09:00`;
      }
      
      const pubDate = new Date(pubStr);
      if (isNaN(pubDate.getTime())) {
        return true; // 不正な日付形式の場合は安全のため表示
      }
      return pubDate <= now;
    } catch (e) {
      return true; // パースエラー時は安全のため表示
    }
  });

  return publishedArticles.sort((a, b) => {
    if (a.publishedAt && b.publishedAt) {
      return a.publishedAt < b.publishedAt ? 1 : -1;
    }
    return 0;
  });
}

/** Get related articles by category (excluding current slug) */
export async function getRelatedArticles(currentSlug: string, category: string, limit = 3): Promise<ArticleItem[]> {
  const allArticles = await getAllArticles();
  const targetNFC = decodeURIComponent(currentSlug).normalize('NFC');
  return allArticles
    .filter(a => a.slug.normalize('NFC') !== targetNFC && a.category === category)
    .slice(0, limit);
}

/** Fetch a single article by slug, preferring Contentful and falling back to markdown. */
export async function getArticleBySlug(slug: string): Promise<ArticleItem | null> {
  const decodedSlug = decodeURIComponent(slug);
  
  // 1️⃣ Try Markdown first with NFC/NFD normalization compatibility fallback
  let foundFileName = '';
  if (fs.existsSync(articlesDirectory)) {
    const files = fs.readdirSync(articlesDirectory);
    const targetNFC = decodedSlug.normalize('NFC');
    const targetNFD = decodedSlug.normalize('NFD');
    
    const matchingFile = files.find(f => {
      if (!f.endsWith('.md')) return false;
      const base = f.replace(/\.md$/, '');
      return base.normalize('NFC') === targetNFC || 
             base.normalize('NFD') === targetNFD || 
             base === decodedSlug;
    });
    if (matchingFile) {
      foundFileName = matchingFile;
    }
  }

  const finalPath = foundFileName 
    ? path.join(articlesDirectory, foundFileName) 
    : path.join(articlesDirectory, `${decodedSlug}.md`);
  
  if (fs.existsSync(finalPath)) {
    const fileContents = fs.readFileSync(finalPath, 'utf8');
    const matterResult = matter(fileContents);
    let content = matterResult.content;

    // Custom markdown transformations (pro/con boxes, rating, affiliate buttons)
    content = content.replace(/\[(?:RATING|総合評価)[：:]\s*([0-9.]+)\]/g, (match, score) => {
      return `<div class="inline-flex items-center gap-1.5 bg-rose-50 text-rose-600 px-4 py-1.5 rounded-full text-xs font-black my-1 border border-rose-100/80"><span class="text-rose-500 text-sm">⭐</span> 総合評価 <span class="text-base font-black text-rose-700">${score}</span></div>`;
    });

    content = content.replace(/:::pro\r?\n([\s\S]*?)\r?\n:::/g,
      '<div class="pro-box"><div class="pro-title">✅ メリット</div>$1</div>');
    content = content.replace(/:::con\r?\n([\s\S]*?)\r?\n:::/g,
      '<div class="con-box"><div class="con-title">⚠️ デメリット</div>$1</div>');

    const ICON = (src: string, alt: string) => `<span class="btn-icon"><img src="${src}" alt="${alt}" width="16" height="16" /></span>`;

    const buildButtons = (productName: string, asin?: string, rakuten?: string, yahoo?: string, prices?: { amazon?: string; rakuten?: string; yahoo?: string }) => {
      const amazonL = asin ? amazonUrl(asin) : amazonSearchUrl(productName);
      const rakutenL = rakuten ? rakutenUrl(rakuten) : `https://search.rakuten.co.jp/search/mall/${encodeURIComponent(productName)}/`;
      const yahooL = yahoo ? yahoo : `https://shopping.yahoo.co.jp/search?p=${encodeURIComponent(productName)}`;

      const btn = (cls: string, url: string, iconSrc: string, label: string, price?: string) =>
        `<a href="${url}" target="_blank" class="${cls}">${ICON(iconSrc, label)}<span class="btn-text-stack"><span class="btn-label">${label}で価格を見る</span></span></a>`;

      return `<div class="affiliate-buttons">
        ${btn('btn-amazon',  amazonL,  'https://www.amazon.co.jp/favicon.ico',       'Amazon',   prices?.amazon)}
        ${btn('btn-rakuten', rakutenL, 'https://www.rakuten.co.jp/favicon.ico',      '楽天市場', prices?.rakuten)}
        ${btn('btn-yahoo',   yahooL,   'https://shopping.yahoo.co.jp/favicon.ico',   'Yahoo!',   prices?.yahoo)}
      </div>`;
    };

    let comparisonTableHtml = '';
    const sections = content.split(/(?=###\s*(?:👑?\s*第\d+位|🌸))/);
    const processedSections = sections.map(section => {
      let s = section;
      const nameMatch = s.match(/###\s*(?:👑?\s*第\d+位:?|🌸)\s*(.*?)(?:\n|$)/i);
      const productName = nameMatch ? nameMatch[1].trim() : decodedSlug;

      const asinMatch = s.match(/ASIN:\s*(https?:\/\/\S+|[A-Z0-9]{10})/i);
      const rakutenMatch = s.match(/RAKUTEN:\s*(https?:\/\/[^\s]+)/i);
      const yahooMatch = s.match(/YAHOO:\s*(https?:\/\/[^\s]+)/i);
      const imageMatch = s.match(/IMAGE:\s*(https?:\/\/[^\s]+)/i);
      const amzPriceMatch = s.match(/AMAZON_PRICE:\s*(\d+)/i);
      const rakPriceMatch = s.match(/RAKUTEN_PRICE:\s*(\d+)/i);
      const yahPriceMatch = s.match(/YAHOO_PRICE:\s*(\d+)/i);

      const asin = asinMatch ? asinMatch[1] : undefined;
      const rakutenRaw = rakutenMatch ? rakutenMatch[1] : undefined;
      const rakuten = rakutenRaw;
      const yahoo = yahooMatch ? yahooMatch[1] : undefined;
      const imageUrl = imageMatch ? imageMatch[1] : undefined;
      
      const prices = {
        amazon: amzPriceMatch ? amzPriceMatch[1] : undefined,
        rakuten: rakPriceMatch ? rakPriceMatch[1] : undefined,
        yahoo: yahPriceMatch ? yahPriceMatch[1] : undefined,
      };

      s = s.replace(/^(?:ASIN|RAKUTEN|YAHOO|IMAGE|AMAZON_PRICE|RAKUTEN_PRICE|YAHOO_PRICE)\s*:.*$/gim, '');
      s = s.replace(/AMAZON_AFFILIATE_URL:\s*https?:\/\/[^\s]+[ \t]*\n?/gi, '');
      s = s.replace(/RAKUTEN_AFFILIATE_URL:\s*https?:\/\/[^\s]+[ \t]*\n?/gi, '');

      if (imageUrl) {
        s = s.replace(/(###\s*(?:👑?\s*第\d+位:?|🌸)[^\n]*\n)/i, `$1<div class="product-image-container"><img src="${imageUrl}" alt="${productName}" class="product-image" referrerpolicy="no-referrer" /></div>\n`);
      }

      const DYNAMIC_BUTTONS = buildButtons(productName, asin, rakuten, yahoo, prices);
      const hasPlaceholder = /\[(AMAZON|RAKUTEN|YAHOO|AFFILIATE)_LINK_HERE\]/i.test(s);
      if (hasPlaceholder) {
        s = s.replace(/\[(?:AMAZON|RAKUTEN|YAHOO|AFFILIATE)_LINK_HERE\](?:\s*\[(?:AMAZON|RAKUTEN|YAHOO|AFFILIATE)_LINK_HERE\])*/gi, DYNAMIC_BUTTONS);
        s = s.replace(/\[(?:AMAZON|RAKUTEN|YAHOO|AFFILIATE)_LINK_HERE\]/gi, '');
      }
      s = s.replace(/(?<!["'])https?:\/\/(?![^<>]*["'])[^\s<)\]]+/gi, '');
      return s;
    });

    content = processedSections.join('\n\n');
    if (comparisonTableHtml) content = comparisonTableHtml + content;

    const processed = await remark()
      .use(remarkGfm)
      .use(html, { sanitize: false })
      .process(content);
    let contentHtml = processed.toString();

    // Improve readability by adding <br /> after Japanese sentence endings (。！？) within paragraphs (<p>)
    // keeping any trailing emojis next to the sentence ending before the line break.
    contentHtml = contentHtml.replace(/<p>([\s\S]*?)<\/p>/g, (match, pContent) => {
      const formatted = pContent.replace(
        /([。！？])([^\u3040-\u309f\u30a0-\u30ff\u4e00-\u9fafA-Za-z0-9\s<]*)(?=[\s\S]*[\u3040-\u309f\u30a0-\u30ff\u4e00-\u9fafA-Za-z0-9])/g,
        "$1$2<br />"
      );
      return `<p>${formatted}</p>`;
    });

    const rankings = parseRankingsFromMarkdown(matterResult.content);

    const actualSlug = foundFileName ? foundFileName.replace(/\.md$/, '') : decodedSlug;
    let coverImage: string | null = null;
    const eyecatchPngPath = path.join(process.cwd(), 'public', 'eyecatch', `${actualSlug}.png`);
    if (fs.existsSync(eyecatchPngPath)) {
      coverImage = `/eyecatch/${actualSlug}.png`;
    } else if (matterResult.data.coverImage) {
      coverImage = matterResult.data.coverImage;
    } else {
      const firstImageMatch = matterResult.content.match(/IMAGE:\s*(https?:\/\/[^\s]+)/i);
      if (firstImageMatch) coverImage = firstImageMatch[1];
    }

    return {
      id: decodedSlug,
      slug: decodedSlug,
      title: matterResult.data.title || decodedSlug,
      coverImage,
      excerpt: matterResult.data.excerpt || '',
      publishedAt: matterResult.data.publishDate || '',
      content: contentHtml,
      rankings: rankings,
      category: matterResult.data.category || '',
      thumbnail: null,
      body: undefined,
    } as ArticleItem;
  }

  // 2️⃣ Try Contentful as fallback
  try {
    const entries = await contentfulClient.getEntries({
      content_type: 'Article',
      'fields.slug': slug,
      limit: 1,
    });
    if (entries.items.length > 0) {
      const f = entries.items[0].fields as any;
      return {
        id: entries.items[0].sys.id,
        title: f.title ?? '',
        slug: f.slug ?? slug,
        category: f.category ?? '',
        excerpt: f.excerpt ?? '',
        thumbnail: f.thumbnail?.fields?.file?.url ?? null,
        publishedAt: f.publishedAt ?? '',
        body: f.body as Document,
        coverImage: f.thumbnail?.fields?.file?.url ?? null,
        rankings: [],
      } as ArticleItem;
    }
  } catch (err) {
    console.error('Contentful fetch error (single):', err);
  }

  return null;
}
