import { getArticleBySlug } from './src/lib/api';

async function main() {
  try {
    console.log("Starting parse test...");
    const article = await getArticleBySlug("20260523-2026年最新日焼け止めおすすめ人気ランキング絶対に焼かない");
    console.log("Success! Title:", article?.title);
    console.log("Rankings count:", article?.rankings.length);
  } catch (err) {
    console.error("CRASHED during parsing:", err);
  }
}

main();
