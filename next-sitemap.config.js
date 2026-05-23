/** @type {import('next-sitemap').IConfig} */
module.exports = {
  siteUrl: 'https://www.mikke-style.com', // Replace with your actual domain
  generateRobotsTxt: true,
  sitemapSize: 7000,
  outDir: 'public',
  additionalPaths: async (config) => {
    const fs = require('fs');
    const path = require('path');
    const articlesDir = path.join(process.cwd(), 'src/content/articles');
    if (!fs.existsSync(articlesDir)) return [];
    
    const files = fs.readdirSync(articlesDir);
    return files
      .filter(f => f.endsWith('.md') && f !== 'GENERATION_RULES.md')
      .map(f => {
        const slug = f.replace(/\.md$/, '');
        return {
          loc: `/articles/${encodeURIComponent(slug)}`,
          changefreq: 'daily',
          priority: 0.7,
          lastmod: new Date().toISOString(),
        };
      });
  }
};
