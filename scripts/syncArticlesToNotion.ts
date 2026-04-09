import fs from 'fs';
import path from 'path';
import matter from 'gray-matter';
import dotenv from 'dotenv';
import { parseRankingsFromMarkdown } from '../src/lib/api';
import { addProductToNotion } from '../src/lib/notion';

dotenv.config({ path: '.env.local' });

const articlesDirectory = path.join(process.cwd(), 'src/content/articles');

async function syncAllArticles() {
  if (!fs.existsSync(articlesDirectory)) {
    console.error(`Articles directory not found: ${articlesDirectory}`);
    return;
  }

  const fileNames = fs.readdirSync(articlesDirectory);
  const articles = fileNames.filter((fn) => fn.endsWith('.md') && fn !== 'GENERATION_RULES.md');

  console.log(`Found ${articles.length} articles to sync...`);

  for (const fn of articles) {
    const fullPath = path.join(articlesDirectory, fn);
    const fileContents = fs.readFileSync(fullPath, 'utf8');
    const { data, content } = matter(fileContents);
    const category = data.category || 'ガジェット';

    const products = parseRankingsFromMarkdown(content);
    console.log(`Syncing ${products.length} products from "${data.title}"...`);

    // Split content by ranking sections to re-extract ASINs for each product
    const sections = content.split(/(?=###[^\n]*第\d+位)/);

    for (const product of products) {
      // Find the corresponding section for this product to get the ASIN
      const section = sections.find(s => s.includes(product.name)) || '';
      const asinMatch = section.match(/ASIN:\s*([A-Z0-9]{10})/i);
      const asin = asinMatch ? asinMatch[1] : '不明';

      try {
        await addProductToNotion({
          articleTitle: data.title,
          name: product.name,
          productNumber: asin,
          category: category,
          amazonUrl: product.amazon?.url || '',
          rakutenUrl: product.rakuten?.url || '',
          yahooUrl: product.yahoo?.url || '',
          status: 'ASINなし',
        });
        console.log(`✅ Synced: ${product.name}`);
      } catch (err) {
        console.error(`❌ Failed: ${product.name}`, err);
      }
    }
  }

  console.log('Sync complete!');
}

syncAllArticles().catch(console.error);
