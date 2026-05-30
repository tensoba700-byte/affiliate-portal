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
      const allElements = Array.from(document.querySelectorAll('*'));
      
      for (const el of allElements) {
        // Skip tags that are scripts, styles, metadata
        const tagName = el.tagName.toLowerCase();
        if (['script', 'style', 'head', 'meta', 'link', 'html', 'body'].includes(tagName)) {
          continue;
        }
        
        const text = el.textContent ? el.textContent.trim() : "";
        if ((text.includes('選び方') || text.includes('選ぶ')) && text.length > 50 && text.length < 500) {
          // Check if this is a leaf-ish node (no child elements that also have text length > 50 containing '選び方')
          const children = Array.from(el.children);
          const hasBigChild = children.some(child => {
            const childTxt = child.textContent ? child.textContent.trim() : "";
            return (childTxt.includes('選び方') || childTxt.includes('選ぶ')) && childTxt.length > 50;
          });
          
          if (!hasBigChild) {
            results.push({
              tag: el.tagName,
              class: el.className,
              text: text.substring(0, 150)
            });
          }
        }
      }
      
      // Let's also check if there is an accordion or list of points
      const points = [];
      const listItems = Array.from(document.querySelectorAll('li, p'));
      for (const li of listItems) {
        const txt = li.textContent.trim();
        if (txt.length > 10 && (txt.includes('光') || txt.includes('波長') || txt.includes('水槽') || txt.includes('サイズ') || txt.includes('タイマー'))) {
          points.push({ tag: li.tagName, text: txt });
        }
      }
      
      return { results: results.slice(0, 50), points: points.slice(0, 20) };
    });
    
    console.log("LEAF ELEMENTS WITH '選び方' OR '選ぶ':");
    console.log(JSON.stringify(elements.results, null, 2));
    
    console.log("\nPOINTS:");
    console.log(JSON.stringify(elements.points, null, 2));
    
  } catch (e) {
    console.error(e);
  } finally {
    await browser.close();
  }
})();
