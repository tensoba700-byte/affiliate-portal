#!/usr/bin/env node
/**
 * generate-eyecatch.js
 * Puppeteer を使って /public/eyecatch/[slug].html を撮影し
 * /public/eyecatch/[slug].png として保存するスクリプト。
 *
 * 使い方: node scripts/generate-eyecatch.js <slug>
 */

const puppeteer = require('puppeteer');
const path = require('path');
const fs = require('fs');

async function main() {
  const slug = process.argv[2];
  if (!slug) {
    console.error('Usage: node scripts/generate-eyecatch.js <slug>');
    process.exit(1);
  }

  const projectRoot = path.resolve(__dirname, '..');
  const htmlPath = path.join(projectRoot, 'public', 'eyecatch', `${slug}.html`);
  const outputPath = path.join(projectRoot, 'public', 'eyecatch', `${slug}.png`);

  if (!fs.existsSync(htmlPath)) {
    console.error(`HTML file not found: ${htmlPath}`);
    process.exit(1);
  }

  console.log(`📸 Screenshotting: ${htmlPath}`);

  const browser = await puppeteer.launch({
    headless: true,
    args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-web-security'],
  });

  try {
    const page = await browser.newPage();
    // Retina-quality output: 2x for crisp display (produces 780x520 actual pixels)
    await page.setViewport({ width: 390, height: 260, deviceScaleFactor: 2 });

    const fileUrl = `file://${htmlPath}`;
    await page.goto(fileUrl, { waitUntil: 'networkidle0', timeout: 20000 });

    // Wait for all images to finish loading (with per-image 5s timeout)
    await page.evaluate(() => {
      return Promise.all(
        Array.from(document.querySelectorAll('img')).map(img => {
          if (img.complete) return Promise.resolve();
          return new Promise(resolve => {
            img.onload = resolve;
            img.onerror = resolve;
            setTimeout(resolve, 5000);
          });
        })
      );
    });

    // Extra settle time for fonts and blends
    await new Promise(r => setTimeout(r, 500));

    await page.screenshot({
      path: outputPath,
      type: 'png',
      clip: { x: 0, y: 0, width: 390, height: 260 },
    });

    console.log(`✅ Eyecatch saved: ${outputPath}`);
  } finally {
    await browser.close();
  }
}

main().catch(err => {
  console.error('❌ Eyecatch generation failed:', err.message);
  process.exit(1);
});
