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
      // Decode any URL-encoded pc= parameter
      const rawUrl = rakutenMatch[1];
      const decoded = rawUrl.replace(/(?<=\?pc=|&pc=)https?%3A%2F%2F[^&\s]*/gi, (encoded) => decodeURIComponent(encoded));
      product.rakuten = { price: '価格を見る', url: decoded };
    }

    // Prices
    const amzPrice = section.match(/AMAZON_PRICE:\s*(\d+)/i);
    const rakPrice = section.match(/RAKUTEN_PRICE:\s*(\d+)/i);
    const yahPrice = section.match(/YAHOO_PRICE:\s*(\d+)/i);
    if (amzPrice && product.amazon) product.amazon.price = `${Number(amzPrice[1]).toLocaleString()}円`;
    if (rakPrice && product.rakuten) product.rakuten.price = `${Number(rakPrice[1]).toLocaleString()}円`;
    if (yahPrice && product.yahoo) product.yahoo.price = `${Number(yahPrice[1]).toLocaleString()}円`;

    products.push(product);
  }
  return products.sort((a, b) => a.rank - b.rank);
}

/** Fetch all articles, preferring Contentful and falling back to local markdown files. */
export async function getAllArticles(): Promise<ArticleItem[]> {
  // 1️⃣ Try Contentful first
  try {
    const entries = await contentfulClient.getEntries({
      content_type: 'Article',
      limit: 1000,
    });
    const cfArticles: ArticleItem[] = entries.items.map((item: any) => {
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
    if (cfArticles.length > 0) {
      console.log(`Fetched ${cfArticles.length} articles from Contentful`);
      return cfArticles;
    }
  } catch (err) {
    console.error('Contentful fetch error (all):', err);
  }

  // 2️⃣ Fallback to local markdown files
  console.log('Fetching articles from local markdown fallback...');
  if (!fs.existsSync(articlesDirectory)) {
    console.warn(`Articles directory not found: ${articlesDirectory}`);
    return [];
  }
  const fileNames = fs.readdirSync(articlesDirectory);
  const now = new Date();
  const twoWeeksMs = 14 * 24 * 60 * 60 * 1000;

  const markdownArticles = fileNames
    .filter((fn) => fn.endsWith('.md') && fn !== 'GENERATION_RULES.md')
    .map((fn) => {
      const slug = fn.replace(/\.md$/, '');
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
    .filter((a) => {
      // Remove restrictive 2-week filter to ensure articles are visible
      return true;
    })
    .sort((a, b) => {
      if (a.publishedAt && b.publishedAt) {
        return a.publishedAt < b.publishedAt ? 1 : -1;
      }
      return 0;
    });

  return markdownArticles;
}

/** Get related articles by category (excluding current slug) */
export async function getRelatedArticles(currentSlug: string, category: string, limit = 3): Promise<ArticleItem[]> {
  const allArticles = await getAllArticles();
  return allArticles
    .filter(a => a.slug !== currentSlug && a.category === category)
    .slice(0, limit);
}

/** Fetch a single article by slug, preferring Contentful and falling back to markdown. */
export async function getArticleBySlug(slug: string): Promise<ArticleItem | null> {
  // 1️⃣ Try Contentful
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

  // 2️⃣ Fallback to markdown
  const decodedSlug = decodeURIComponent(slug);
  const fullPath = path.join(articlesDirectory, `${decodedSlug}.md`);
  if (!fs.existsSync(fullPath)) return null;
  const fileContents = fs.readFileSync(fullPath, 'utf8');
  const matterResult = matter(fileContents);
  let content = matterResult.content;

  // Custom markdown transformations (pro/con boxes, rating, affiliate buttons)
  content = content.replace(/:::pro\n([\s\S]*?)\n:::/g,
    '<div class="pro-box"><div class="pro-title">✅ メリット</div>$1</div>');
  content = content.replace(/:::con\n([\s\S]*?)\n:::/g,
    '<div class="con-box"><div class="pro-title">⚠️ デメリット</div>$1</div>');
  content = content.replace(/\[(?:RATING|総合評価):\s*([0-9.]+)\]/g, (m, p1) => {
    const score = parseFloat(p1);
    return `<div class="rating-container"><span>総合評価:</span> <span class="stars">${'★'.repeat(Math.floor(score))}${'☆'.repeat(5 - Math.floor(score))}</span> <span class="score">${score}</span></div>`;
  });

  const ICON = (src: string, alt: string) => `<span class="btn-icon"><img src="${src}" alt="${alt}" width="16" height="16" /></span>`;

  // Helper to build a set of affiliate buttons dynamically
  const buildButtons = (productName: string, asin?: string, rakuten?: string, yahoo?: string, prices?: { amazon?: string; rakuten?: string; yahoo?: string }) => {
    const amazonL = asin ? amazonUrl(asin) : amazonSearchUrl(productName);
    const rakutenL = rakuten ? rakutenUrl(rakuten) : `https://search.rakuten.co.jp/search/mall/${encodeURIComponent(productName)}/`;
    const yahooL = yahoo ? yahoo : `https://shopping.yahoo.co.jp/search?p=${encodeURIComponent(productName)}`;

    const formatPrice = (p?: string) => (p && p !== '0' ? ` ${Number(p).toLocaleString()}円` : '');

    return `<div class="affiliate-buttons">
      <a href="${amazonL}" target="_blank" class="btn-amazon">${ICON('https://www.amazon.co.jp/favicon.ico', 'Amazon')} Amazonで見る${formatPrice(prices?.amazon)}</a>
      <a href="${rakutenL}" target="_blank" class="btn-rakuten">${ICON('https://www.rakuten.co.jp/favicon.ico', '楽天')} 楽天市場で見る${formatPrice(prices?.rakuten)}</a>
      <a href="${yahooL}" target="_blank" class="btn-yahoo">${ICON('https://shopping.yahoo.co.jp/favicon.ico', 'Yahoo')} Yahoo!で見る${formatPrice(prices?.yahoo)}</a>
    </div>`;
  };

  // Divide content into sections by rank headings to ensure buttons match the correct item
  const sections = content.split(/(?=###\s*👑?\s*第\d+位)/);
  const processedSections = sections.map(section => {
    let s = section;
    
    // Extract product name from heading (e.g. "### 👑 第1位: ダイソン 掃除機" -> "ダイソン 掃除機")
    const nameMatch = s.match(/第\d+位:?\s*(.*?)(?:\n|$)/i);
    const productName = nameMatch ? nameMatch[1].trim() : decodedSlug;

    // Find identifiers SPECIFIC to this section
    // ASIN: accepts both a full affiliate URL and a bare 10-char ASIN code
    const asinMatch = s.match(/ASIN:\s*(https?:\/\/\S+|[A-Z0-9]{10})/i);
    const rakutenMatch = s.match(/RAKUTEN:\s*(https?:\/\/[^\s]+)/i);
    const yahooMatch = s.match(/YAHOO:\s*(https?:\/\/[^\s]+)/i);
    const imageMatch = s.match(/IMAGE:\s*(https?:\/\/[^\s]+)/i);
    const amzPriceMatch = s.match(/AMAZON_PRICE:\s*(\d+)/i);
    const rakPriceMatch = s.match(/RAKUTEN_PRICE:\s*(\d+)/i);
    const yahPriceMatch = s.match(/YAHOO_PRICE:\s*(\d+)/i);

    const asin = asinMatch ? asinMatch[1] : undefined;
    // Decode url-encoded Rakuten URLs (pc=https%3A%2F%2F... → pc=https://...)
    const rakutenRaw = rakutenMatch ? rakutenMatch[1] : undefined;
    const rakuten = rakutenRaw
      ? rakutenRaw.replace(/(?<=\?pc=|&pc=)https?%3A%2F%2F[^&\s]*/gi, (enc) => decodeURIComponent(enc))
      : undefined;
    const yahoo = yahooMatch ? yahooMatch[1] : undefined;
    const imageUrl = imageMatch ? imageMatch[1] : undefined;
    
    const prices = {
      amazon: amzPriceMatch ? amzPriceMatch[1] : undefined,
      rakuten: rakPriceMatch ? rakPriceMatch[1] : undefined,
      yahoo: yahPriceMatch ? yahPriceMatch[1] : undefined,
    };

    // Remove all identifier/metadata lines from final HTML
    s = s.replace(/ASIN:\s*(?:https?:\/\/\S+|[A-Z0-9]{10})[ \t]*\n?/gi, '');
    s = s.replace(/RAKUTEN:\s*https?:\/\/[^\s]+[ \t]*\n?/gi, '');
    s = s.replace(/YAHOO:\s*https?:\/\/[^\s]+[ \t]*\n?/gi, '');
    s = s.replace(/IMAGE:\s*https?:\/\/[^\s]+[ \t]*\n?/gi, '');
    s = s.replace(/AMAZON_PRICE:\s*\d+[ \t]*\n?/gi, '');
    s = s.replace(/RAKUTEN_PRICE:\s*\d+[ \t]*\n?/gi, '');
    s = s.replace(/YAHOO_PRICE:\s*\d+[ \t]*\n?/gi, '');
    s = s.replace(/AMAZON_AFFILIATE_URL:\s*https?:\/\/[^\s]+[ \t]*\n?/gi, '');
    s = s.replace(/RAKUTEN_AFFILIATE_URL:\s*https?:\/\/[^\s]+[ \t]*\n?/gi, '');

    // Add Image Tag if present, right after the heading
    if (imageUrl) {
      s = s.replace(/(###\s*👑?\s*第\d+位:?[^\n]*\n)/i, `$1\n<div class="product-image-container"><img src="${imageUrl}" alt="${productName}" class="product-image" /></div>\n`);
    }

    // Replace placeholders with dynamic buttons for THIS section
    const DYNAMIC_BUTTONS = buildButtons(productName, asin, rakuten, yahoo, prices);
    
    // Check if any placeholder exists (case-insensitive)
    const hasPlaceholder = /\[(AMAZON|RAKUTEN|YAHOO|AFFILIATE)_LINK_HERE\]/i.test(s);
    
    if (hasPlaceholder) {
      // 1. Replace the first cluster of placeholders with the full button set
      s = s.replace(/\[(?:AMAZON|RAKUTEN|YAHOO|AFFILIATE)_LINK_HERE\](?:\s*\[(?:AMAZON|RAKUTEN|YAHOO|AFFILIATE)_LINK_HERE\])*/i, DYNAMIC_BUTTONS);
      // 2. Clean up any remaining single placeholders in the same section to prevent duplicates
      s = s.replace(/\[(?:AMAZON|RAKUTEN|YAHOO|AFFILIATE)_LINK_HERE\]/gi, '');
    }

    // Strip any remaining raw URLs NOT inside an HTML attribute (href/src)
    s = s.replace(/(?<!["'])https?:\/\/(?![^<>]*["'])[^\s<)\]]+/gi, '');

    return s;
  });

  content = processedSections.join('\n\n');

  const processed = await remark()
    .use(remarkGfm)
    .use(html, { sanitize: false })
    .process(content);
  const contentHtml = processed.toString();

  const rankings = parseRankingsFromMarkdown(matterResult.content);
  // Enrich rankings with Yahoo API data and Unsplash images
  for (const product of rankings) {
    const [yahooData, imageUrl] = await Promise.all([
      fetchYahooProduct(product.name),
      fetchUnsplashImage(product.name),
    ]);
    if (yahooData) {
      product.yahoo = { price: yahooData.price, url: yahooData.url };
    }
    if (imageUrl) {
      product.imageUrl = imageUrl;
    }
  }

  // Priority: eyecatch PNG > frontmatter coverImage > first IMAGE: tag
  let coverImage: string | null = null;
  const eyecatchPngPath = path.join(process.cwd(), 'public', 'eyecatch', `${decodedSlug}.png`);
  if (fs.existsSync(eyecatchPngPath)) {
    coverImage = `/eyecatch/${decodedSlug}.png`;
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
