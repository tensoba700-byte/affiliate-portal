import { getArticleBySlug } from './src/lib/api';

async function main() {
  try {
    console.log("Fetching test article (booster)...");
    const article = await getArticleBySlug("20260618-affordable-booster");
    if (!article) {
      console.log("Article not found!");
      return;
    }
    console.log(`Title: "${article.title}"`);
    console.log(`Rankings length: ${article.rankings.length}`);
    for (const r of article.rankings) {
      console.log(`Rank: ${r.rank} | Name: "${r.name}" | Score: ${r.score}`);
    }
  } catch (err) {
    console.error("CRASHED:", err);
  }
}

main();
