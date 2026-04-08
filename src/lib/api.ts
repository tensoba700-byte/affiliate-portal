import fs from 'fs';
import path from 'path';
import matter from 'gray-matter';
import { remark } from 'remark';
import html from 'remark-html';

import type { Document } from '@contentful/rich-text-types';
import { contentfulClient } from '@/src/lib/contentful';

import type { Product } from '@/src/components/RankingTable';

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
 * Parse ranking sections from raw markdown content.
 * Looks for headings like "### 👑 第1位: 商品名" and rating tags like "[総合評価: 4.5]".
 */
function parseRankingsFromMarkdown(raw: string): Product[] {
  const products: Product[] = [];
  const sections = raw.split(/(?=###[^\n]*第\d+位)/);
  for (const section of sections) {
    const rankMatch = section.match(/第(\d+)位[：:]\s*(.+)/);
    if (!rankMatch) continue;
    const rank = parseInt(rankMatch[1], 10);
    if (rank > 6) continue; // limit to top 6
    const name = rankMatch[2].replace(/\*\*/g, '').trim();
    const ratingMatch = section.match(/\[(?:RATING|総合評価)[：:]\s*([0-9.]+)\]/);
    const score = ratingMatch ? parseFloat(ratingMatch[1]) : 4.0;
    const q = encodeURIComponent(name);
    products.push({
      rank,
      brand: '',
      name,
      imageUrl: '',
      score,
      amazon: { price: '価格を見る', url: `https://www.amazon.co.jp/s?k=${q}` },
      yahoo: { price: '価格を見る', url: `https://shopping.yahoo.co.jp/search?p=${q}` },
      rakuten: { price: '価格を見る', url: `https://search.rakuten.co.jp/search/mall/${q}/` },
    });
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
    .filter((fn) => fn.endsWith('.md'))
    .map((fn) => {
      const slug = fn.replace(/\.md$/, '');
      const fullPath = path.join(articlesDirectory, fn);
      const fileContents = fs.readFileSync(fullPath, 'utf8');
      const matterResult = matter(fileContents);
      return {
        id: slug,
        slug,
        title: matterResult.data.title || slug,
        coverImage: matterResult.data.coverImage || null,
        excerpt: matterResult.data.excerpt || '',
        publishedAt: matterResult.data.publishDate || now.toISOString(),
        content: matterResult.content,
        rankings: [],
        thumbnail: null,
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
  const BOTH_BUTTONS = `<div class="affiliate-buttons"><a href="https://amazon.co.jp/" target="_blank" class="btn-amazon">${ICON('https://www.amazon.co.jp/favicon.ico','Amazon')} Amazonで見る</a><a href="https://rakuten.co.jp/" target="_blank" class="btn-rakuten">${ICON('https://www.rakuten.co.jp/favicon.ico','楽天')} 楽天市場で見る</a><a href="" target="_blank" class="btn-yahoo">${ICON('https://shopping.yahoo.co.jp/favicon.ico','Yahoo')} Yahoo!で見る</a></div>`;
  content = content.replace(/\[AMAZON_LINK_HERE\]\s*\[RAKUTEN_LINK_HERE\]/g, BOTH_BUTTONS);
  content = content.replace(/\[RAKUTEN_LINK_HERE\]\s*\[AMAZON_LINK_HERE\]/g, BOTH_BUTTONS);
  content = content.replace(/\[AMAZON_LINK_HERE\]/g, BOTH_BUTTONS);
  content = content.replace(/\[RAKUTEN_LINK_HERE\]/g, BOTH_BUTTONS);

  const processed = await remark().use(html, { sanitize: false }).process(content);
  const contentHtml = processed.toString();

  return {
    id: decodedSlug,
    slug: decodedSlug,
    title: matterResult.data.title || decodedSlug,
    coverImage: matterResult.data.coverImage || null,
    excerpt: matterResult.data.excerpt || '',
    publishedAt: matterResult.data.publishDate || '',
    content: contentHtml,
    rankings: parseRankingsFromMarkdown(matterResult.content),
    category: matterResult.data.category || '',
    thumbnail: null,
    body: undefined,
  } as ArticleItem;
}
