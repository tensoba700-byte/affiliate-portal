/** @type {import('next-sitemap').IConfig} */
module.exports = {
  siteUrl: 'https://www.mikke-style.com',
  generateRobotsTxt: true,
  sitemapSize: 7000,
  outDir: 'public',
  // Percent-encode and NFC normalize all paths generated in the sitemap to prevent invalid XML or duplicate issues
  transform: async (config, path) => {
    // Decode first to prevent double encoding, and normalize to NFC
    const decoded = decodeURIComponent(path).normalize('NFC');
    
    // Percent-encode each segment of the path individually to preserve slashes
    const segments = decoded.split('/').map(seg => encodeURIComponent(seg));
    const cleanPath = segments.join('/').replace(/%3A/g, ':'); // Restore colons if any (like http:)
    
    return {
      loc: cleanPath,
      changefreq: config.changefreq,
      priority: config.priority,
      lastmod: config.autoLastmod ? new Date().toISOString() : undefined,
      alternateRefs: config.alternateRefs ?? [],
    };
  }
};
