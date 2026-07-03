#!/usr/bin/env node
/**
 * generate-pinterest-eyecatch.js
 * Puppeteer を使って /public/eyecatch/[slug]-pin.html を撮影し
 * /public/eyecatch/[slug]-pin.png として保存するスクリプト（アスペクト比 2:3）。
 *
 * 使い方: node scripts/generate-pinterest-eyecatch.js <slug>
 */

const puppeteer = require('puppeteer');
const path = require('path');
const fs = require('fs');

async function main() {
  const slug = process.argv[2];
  if (!slug) {
    console.error('Usage: node scripts/generate-pinterest-eyecatch.js <slug>');
    process.exit(1);
  }

  const projectRoot = path.resolve(__dirname, '..');
  const htmlPath = path.join(projectRoot, 'public', 'eyecatch', `${slug}-pin.html`);
  const outputPath = path.join(projectRoot, 'public', 'eyecatch', `${slug}-pin.png`);

  if (!fs.existsSync(htmlPath)) {
    console.error(`HTML file not found: ${htmlPath}`);
    process.exit(1);
  }

  console.log(`📸 Screenshotting vertical pin: ${htmlPath}`);

  const browser = await puppeteer.launch({
    headless: true,
    args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-web-security'],
  });

  try {
    const page = await browser.newPage();
    // 1000x1500 (2:3 aspect ratio)
    await page.setViewport({ width: 1000, height: 1500, deviceScaleFactor: 1 });

    const fileUrl = `file://${htmlPath}`;
    await page.goto(fileUrl, { waitUntil: 'networkidle0', timeout: 30000 });

    // Wait for images
    await page.evaluate(async () => {
      const images = Array.from(document.querySelectorAll('img'));
      console.log(`Waiting for ${images.length} images to load...`);
      
      const results = await Promise.allSettled(
        images.map(async (img) => {
          if (img.complete && img.naturalWidth > 0) {
            return { src: img.src, success: true };
          }
          
          await new Promise((resolve) => {
            if (img.complete) { resolve(); return; }
            const onDone = () => resolve();
            img.addEventListener('load', onDone, { once: true });
            img.addEventListener('error', onDone, { once: true });
            setTimeout(resolve, 15000);
          });
          
          if (typeof img.decode === 'function') {
            await img.decode().catch(() => {});
          }
          
          const success = img.complete && img.naturalWidth > 0;
          return { src: img.src, success };
        })
      );
      
      const failed = results
        .map((r, i) => {
          if (r.status === 'rejected') return { src: images[i].src, reason: 'rejected' };
          if (!r.value.success) return { src: r.value.src, reason: 'blank/404' };
          return null;
        })
        .filter(Boolean);
        
      if (failed.length > 0) {
        const errorMsg = failed.map(f => `- ${f.src} (${f.reason})`).join('\n');
        throw new Error(`Some images failed to load:\n${errorMsg}`);
      }
    });

    await new Promise(r => setTimeout(r, 800));

    await page.screenshot({
      path: outputPath,
      type: 'png',
      clip: { x: 0, y: 0, width: 1000, height: 1500 },
    });

    console.log(`✅ Pinterest Eyecatch saved: ${outputPath}`);
  } finally {
    await browser.close();
  }
}

main().catch(err => {
  console.error('❌ Pinterest Eyecatch generation failed:', err.message);
  process.exit(1);
});
