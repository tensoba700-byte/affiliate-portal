import fs from 'fs';
import path from 'path';
import { getAllArticles } from '../src/lib/api';

async function generateFeed() {
  console.log('🔄 Generating RSS feed (feed.xml)...');
  try {
    const articles = await getAllArticles();
    // Get top 20 latest articles
    const latestArticles = articles.slice(0, 20);

    const siteUrl = 'https://www.mikke-style.com';
    const feedPath = path.join(process.cwd(), 'public', 'feed.xml');

    let rssXml = `<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">
  <channel>
    <title>みっけ！ - 徹底比較のおすすめ人気ランキング</title>
    <link>${siteUrl}</link>
    <description>みっけ！は、忙しい人のための徹底比較・おすすめ商品紹介ポータルサイトです。</description>
    <language>ja</language>
    <lastBuildDate>${new Date().toUTCString()}</lastBuildDate>
    <atom:link href="${siteUrl}/feed.xml" rel="self" type="application/rss+xml" />
`;

    for (const article of latestArticles) {
      const pubDate = new Date(article.publishedAt || '').toUTCString();
      // Percent-encode the URL slug properly, normalized to NFC
      const normalizedSlug = encodeURIComponent(article.slug.normalize('NFC'));
      const articleUrl = `${siteUrl}/articles/${normalizedSlug}`;
      const description = article.excerpt || '';
      
      rssXml += `    <item>
      <title><![CDATA[${article.title.replace(/<br\s*\/?>/gi, '')}]]></title>
      <link>${articleUrl}</link>
      <guid>${articleUrl}</guid>
      <pubDate>${pubDate}</pubDate>
      <description><![CDATA[${description}]]></description>
    </item>\n`;
    }

    rssXml += `  </channel>
</rss>`;

    fs.writeFileSync(feedPath, rssXml, 'utf8');
    console.log(`✅ RSS feed generated successfully at: ${feedPath}`);
  } catch (err) {
    console.error('❌ Failed to generate RSS feed:', err);
  }
}

generateFeed();
