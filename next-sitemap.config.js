/** @type {import('next-sitemap').IConfig} */
const fs = require('fs');
const path = require('path');

module.exports = {
  siteUrl: 'https://www.mikke-style.com',
  generateRobotsTxt: true,
  robotsTxtOptions: {
    transformRobotsTxt: async (config, robotsTxt) => {
      return robotsTxt + '\nSitemap: https://www.mikke-style.com/feed.xml';
    },
  },
  sitemapSize: 7000,
  exclude: ['/sample', '/sample/*'],
  outDir: 'public',
  // 記事URLをMarkdownファイルから直接生成（generateStaticParamsが動かない環境でも確実に全記事をサイトマップに含める）
  additionalPaths: async (config) => {
    const articlesDir = path.join(process.cwd(), 'src', 'content', 'articles');
    if (!fs.existsSync(articlesDir)) return [];

    const mdFiles = fs.readdirSync(articlesDir).filter(
      (f) => f.endsWith('.md') && f !== 'GENERATION_RULES.md' && !f.includes('-fix')
    );

    return mdFiles.map((file) => {
      const slug = file.replace(/\.md$/, '').normalize('NFC');
      const encodedSlug = slug.split('').map(c => {
        // ASCII英数字・ハイフン・アンダースコア・ドットはそのまま
        if (/[\w\-._~]/.test(c)) return c;
        return encodeURIComponent(c);
      }).join('');

      return {
        loc: `/articles/${encodedSlug}`,
        changefreq: 'weekly',
        priority: 0.8,
        lastmod: new Date().toISOString(),
      };
    });
  },
  transform: async (config, path) => {
    const decoded = decodeURIComponent(path).normalize('NFC');
    const segments = decoded.split('/').map(seg => encodeURIComponent(seg));
    const cleanPath = segments.join('/').replace(/%3A/g, ':');

    return {
      loc: cleanPath,
      changefreq: config.changefreq,
      priority: config.priority,
      lastmod: config.autoLastmod ? new Date().toISOString() : undefined,
      alternateRefs: config.alternateRefs ?? [],
    };
  },
};
