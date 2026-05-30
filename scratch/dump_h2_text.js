const puppeteer = require('puppeteer');

(async () => {
  const browser = await puppeteer.launch({
    headless: true,
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });
  const page = await browser.newPage();
  await page.setUserAgent('Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/120.0.0.0');
  
  try {
    console.log("Navigating to page...");
    await page.goto('https://my-best.com/21509', { waitUntil: 'networkidle2', timeout: 30000 });
    await new Promise(r => setTimeout(r, 2000));
    
    const elements = await page.evaluate(() => {
      const results = [];
      const h2s = Array.from(document.querySelectorAll('h2'));
      for (const h2 of h2s) {
        const text = h2.textContent.trim();
        const content = [];
        let next = h2.nextElementSibling;
        while (next) {
          if (next.tagName.toLowerCase() === 'h2') break;
          const txt = next.textContent.trim();
          if (txt) {
            content.push(txt.substring(0, 100));
          }
          next = next.nextElementSibling;
          if (content.length > 5) break;
        }
        results.push({
          heading: text,
          content: content
        });
      }
      return results;
    });
    
    console.log("H2 SECTIONS:");
    console.log(JSON.stringify(elements, null, 2));
    
  } catch (e) {
    console.error(e);
  } finally {
    await browser.close();
  }
})();
