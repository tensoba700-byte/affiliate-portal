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

    for (const product of products) {
      try {
        await addProductToNotion({
          articleTitle: data.title,
          name: product.name,
          category: category,
          amazonUrl: '',
          rakutenUrl: '',
          yahooUrl: '',
          status: '未処理',
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
