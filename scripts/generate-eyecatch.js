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
    // 1200x630 direct output
    await page.setViewport({ width: 1200, height: 630, deviceScaleFactor: 1 });

    const fileUrl = `file://${htmlPath}`;
    // ページ読み込み: networkidle0 で初期リクエストが完了するまで待機
    await page.goto(fileUrl, { waitUntil: 'networkidle0', timeout: 30000 });

    // 全商品画像の読み込み完了を確実に待機し、エラーがあれば検知する
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
            setTimeout(resolve, 15000); // 15s timeout
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
        throw new Error(`Some images failed to load or are blank (404/CORS/error):\n${errorMsg}`);
      }
      
      console.log('All images loaded successfully.');
    });

    // フォント・mix-blend-mode のレンダリングが落ち着くまで追加待機
    await new Promise(r => setTimeout(r, 800));

    await page.screenshot({
      path: outputPath,
      type: 'png',
      clip: { x: 0, y: 0, width: 1200, height: 630 },
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
