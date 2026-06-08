const puppeteer = require('puppeteer');
const path = require('path');
const fs = require('fs');

(async () => {
  console.log("Launching browser...");
  const browser = await puppeteer.launch({
    headless: true,
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });
  const page = await browser.newPage();
  
  // Set viewport to desktop size
  await page.setViewport({ width: 1280, height: 1200 });

  const artifactDir = '/Users/tsukika/.gemini/antigravity/brain/36cd6800-ea09-4139-b298-e3adf48dce72';

  const targets = [
    { name: 'homepage_screenshot.png', url: 'http://localhost:3000/' },
    { name: 'articles_screenshot.png', url: 'http://localhost:3000/articles' },
    { name: 'article_detail_screenshot.png', url: 'http://localhost:3000/articles/20260607-cleansing-oil' }
  ];

  for (const target of targets) {
    try {
      console.log(`Navigating to ${target.url}...`);
      await page.goto(target.url, { waitUntil: 'networkidle2', timeout: 15000 });

      // Force apply clean-science theme in client browser
      await page.evaluate(() => {
        document.documentElement.setAttribute('data-theme', 'clean-science');
        document.documentElement.setAttribute('data-font', 'sans');
        localStorage.setItem('mikke-theme', 'clean-science');
        localStorage.setItem('mikke-font', 'sans');
      });

      // Wait a moment for styles to apply
      await page.evaluate(() => new Promise(resolve => setTimeout(resolve, 800)));

      const savePath = path.join(artifactDir, target.name);
      await page.screenshot({ path: savePath });
      console.log(`Saved screenshot to ${savePath}`);
    } catch (err) {
      console.error(`Failed to capture ${target.url}:`, err.message);
    }
  }

  await browser.close();
  console.log("All screenshots captured successfully.");
})();
