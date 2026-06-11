import fs from 'fs';
import path from 'path';
import matter from 'gray-matter';
import { remark } from 'remark';
import html from 'remark-html';
import remarkGfm from 'remark-gfm';

const columnsDirectory = path.join(process.cwd(), 'src/content/columns');

export interface ColumnItem {
  slug: string;
  title: string;
  description: string;
  category: string;
  publishDate: string; // "YYYY-MM-DD HH:mm:ss"
  contentHtml: string;
  headings: { text: string; id: string }[];
  faq: { question: string; answer: string }[];
  summary: string;
  related_articles: string[];
  coverImage: string;
}

// 記事のslugからハッシュ値を作成し、5枚の画像から自動割り当て
export function getPlaceholderImage(slug: string): string {
  let hash = 0;
  for (let i = 0; i < slug.length; i++) {
    hash = slug.charCodeAt(i) + ((hash << 5) - hash);
  }
  const index = (Math.abs(hash) % 5) + 1; // 1〜5
  return `/column-images/cover_${index}.png`;
}

export async function getAllColumns(): Promise<ColumnItem[]> {
  if (!fs.existsSync(columnsDirectory)) {
    return [];
  }
  const fileNames = fs.readdirSync(columnsDirectory);
  const now = new Date();

  const columns = await Promise.all(
    fileNames
      .filter((fn) => fn.endsWith('.md'))
      .map(async (fn) => {
        const slug = fn.replace(/\.md$/, '');
        return await getColumnBySlug(slug);
      })
  );

  const validColumns = columns.filter((c): c is ColumnItem => c !== null);

  // 公開日時フィルタ適用
  const publishedColumns = validColumns.filter((c) => {
    if (!c.publishDate) return true;
    try {
      let pubStr = c.publishDate.trim();
      if (/^\d{4}-\d{2}-\d{2}$/.test(pubStr)) {
        pubStr = `${pubStr}T07:00:00+09:00`;
      } else if (/^\d{4}-\d{2}-\d{2}\s\d{2}:\d{2}$/.test(pubStr)) {
        pubStr = `${pubStr.replace(' ', 'T')}:00+09:00`;
      } else if (/^\d{4}-\d{2}-\d{2}\s\d{2}:\d{2}:\d{2}$/.test(pubStr)) {
        pubStr = `${pubStr.replace(' ', 'T')}+09:00`;
      }
      const pubDate = new Date(pubStr);
      if (isNaN(pubDate.getTime())) return true;
      return pubDate <= now;
    } catch (e) {
      return true;
    }
  });

  // 新しい順（日付降順）にソート
  return publishedColumns.sort((a, b) => {
    return b.publishDate.localeCompare(a.publishDate);
  });
}

export async function getColumnBySlug(slug: string): Promise<ColumnItem | null> {
  const decodedSlug = decodeURIComponent(slug);
  const fullPath = path.join(columnsDirectory, `${decodedSlug}.md`);
  if (!fs.existsSync(fullPath)) {
    return null;
  }

  try {
    const fileContents = fs.readFileSync(fullPath, 'utf8');
    const matterResult = matter(fileContents);
    const data = matterResult.data;
    const rawContent = matterResult.content;

    // HTMLへのレンダリング
    const processedContent = await remark()
      .use(remarkGfm)
      .use(html, { sanitize: false })
      .process(rawContent);
    let contentHtml = processedContent.toString();

    // 改行等の整形 (api.ts準拠)
    contentHtml = contentHtml.replace(/<p>([\s\S]*?)<\/p>/g, (match, pContent) => {
      const formatted = pContent.replace(
        /([。！？])([^\u3040-\u309f\u30a0-\u30ff\u4e00-\u9fafA-Za-z0-9\s<]*)(?=[\s\S]*[\u3040-\u309f\u30a0-\u30ff\u4e00-\u9fafA-Za-z0-9])/g,
        "$1$2<br />"
      );
      return `<p>${formatted}</p>`;
    });

    // h2見出しを抽出してIDを付与する（目次用）
    const headings: { text: string; id: string }[] = [];
    let headingIndex = 0;
    contentHtml = contentHtml.replace(/<h2>(.*?)<\/h2>/g, (match, headingText) => {
      const cleanText = headingText.replace(/<[^>]*>/g, '').trim();
      const id = `heading-${headingIndex++}`;
      headings.push({ text: cleanText, id });
      return `<h2 id="${id}">${headingText}</h2>`;
    });

    // FAQのパース
    const faq: { question: string; answer: string }[] = [];
    const faqRegex = /###\s*(.*?)\r?\n\s*([\s\S]*?)(?=\r?\n###|\r?\n##|$)/g;
    const faqSectionMatch = rawContent.match(/##\s*❓\s*よくある質問（FAQ）\r?\n([\s\S]*?)(?=\n##|$)/);
    if (faqSectionMatch) {
      const faqText = faqSectionMatch[1];
      let match;
      while ((match = faqRegex.exec(faqText)) !== null) {
        const question = match[1].trim();
        const answer = match[2].trim();
        if (question && answer) {
          faq.push({ question, answer });
        }
      }
    }

    // summaryのパース
    let summary = '';
    const summaryMatch = rawContent.match(/##\s*💬\s*まとめ\r?\n([\s\S]*?)(?=\r?\n---|\r?\n##|$)/);
    if (summaryMatch) {
      summary = summaryMatch[1].trim();
    }

    // related_articlesのパース
    const related_articles: string[] = [];
    const relatedMatch = rawContent.match(/\*\*あわせて読みたいおすすめ比較記事\*\*\r?\n([\s\S]*?)$/);
    if (relatedMatch) {
      const lines = relatedMatch[1].split('\n');
      for (const line of lines) {
        const m = line.match(/-\s*\[.*?\]\(\/articles\/(.*?)\)/);
        if (m) {
          related_articles.push(m[1].trim());
        }
      }
    }

    const coverImage = data.eyecatch || data.coverImage || getPlaceholderImage(decodedSlug);

    return {
      slug: decodedSlug,
      title: data.title || '',
      description: data.description || '',
      category: data.category || '',
      publishDate: data.publishDate || '',
      contentHtml,
      headings,
      faq,
      summary,
      related_articles,
      coverImage
    };
  } catch (e) {
    console.error(`Error loading column ${slug}:`, e);
    return null;
  }
}
