import { getAllArticles } from './src/lib/api';

async function main() {
  try {
    console.log("Fetching all articles...");
    const articles = await getAllArticles();
    console.log(`Fetched ${articles.length} articles.`);
    for (let i = 0; i < Math.min(10, articles.length); i++) {
      const a = articles[i];
      console.log(`[${i}] Title: "${a.title}" | Slug: "${a.slug}" | PublishedAt: "${a.publishedAt}"`);
    }
  } catch (err) {
    console.error("CRASHED:", err);
  }
}

main();
