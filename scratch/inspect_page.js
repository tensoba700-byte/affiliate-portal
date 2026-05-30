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
      const headings = Array.from(document.querySelectorAll('h1, h2, h3, h4, h5')).map(h => ({
        tag: h.tagName,
        text: h.textContent.trim()
      }));
      
      // Let's also search for any element containing "選び方" or "選ぶ"
      const elText = [];
      const allDivs = Array.from(document.querySelectorAll('div, section, p, span, h2, h3'));
      for (const el of allDivs) {
        const txt = el.textContent ? el.textContent.trim() : "";
        if (txt.includes('選び方') && txt.length > 5 && txt.length < 100) {
          elText.push({
            tag: el.tagName,
            class: el.className,
            text: txt
          });
        }
      }
      
      return { headings, elText: elText.slice(0, 30) };
    });
    
    console.log("HEADINGS:");
    console.log(JSON.stringify(elements.headings, null, 2));
    
    console.log("\nELEMENTS CONTAINING '選び方':");
    console.log(JSON.stringify(elements.elText, null, 2));
    
  } catch (e) {
    console.error(e);
  } finally {
    await browser.close();
  }
})();
