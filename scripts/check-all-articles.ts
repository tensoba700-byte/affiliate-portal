import fs from 'fs';
import path from 'path';

async function main() {
  const sitemapPath = path.join(__dirname, '../public/sitemap-0.xml');
  if (!fs.existsSync(sitemapPath)) {
    console.error("Sitemap file not found at:", sitemapPath);
    process.exit(1);
  }

  const content = fs.readFileSync(sitemapPath, 'utf8');
  // Extract all <loc> values
  const matches = content.match(/<loc>(https?:\/\/[^<]+)<\/loc>/g);
  if (!matches) {
    console.error("No URLs found in sitemap.");
    process.exit(1);
  }

  const urls = matches.map(m => m.replace(/<\/?loc>/g, '').trim());
  // Filter for article detail URLs
  const articleUrls = urls.filter(url => url.includes('/articles/'));

  console.log(`🔍 Found ${articleUrls.length} article URLs in sitemap. Starting health check...`);

  const results: { url: string; status: number; ok: boolean }[] = [];

  for (let i = 0; i < articleUrls.length; i++) {
    const url = articleUrls[i];
    // Encode the Japanese characters properly for HTTP fetch
    const parsed = new URL(url);
    const encodedUrl = `${parsed.protocol}//${parsed.host}${parsed.pathname.split('/').map(p => encodeURIComponent(decodeURIComponent(p))).join('/')}${parsed.search}`;
    
    try {
      const res = await fetch(encodedUrl, { method: 'HEAD' });
      results.push({ url, status: res.status, ok: res.status === 200 });
      console.log(`[${i + 1}/${articleUrls.length}] ${res.status === 200 ? '✅' : '❌'} ${res.status} - ${decodeURIComponent(url)}`);
    } catch (err: any) {
      results.push({ url, status: 0, ok: false });
      console.log(`[${i + 1}/${articleUrls.length}] ❌ ERROR - ${decodeURIComponent(url)}: ${err.message}`);
    }
  }

  const failures = results.filter(r => !r.ok);
  console.log("\n==========================================");
  console.log(`📊 Health Check Completed:`);
  console.log(`   - Total Checked: ${articleUrls.length}`);
  console.log(`   - Success (200 OK): ${articleUrls.length - failures.length}`);
  console.log(`   - Failures: ${failures.length}`);
  console.log("==========================================");

  if (failures.length > 0) {
    console.log("❌ The following URLs failed:");
    failures.forEach(f => {
      console.log(`   - [Status: ${f.status}] ${decodeURIComponent(f.url)}`);
    });
    process.exit(1);
  } else {
    console.log("✨ All checked articles returned 200 OK!");
  }
}

main().catch(err => {
  console.error("Fatal error during execution:", err);
  process.exit(1);
});
