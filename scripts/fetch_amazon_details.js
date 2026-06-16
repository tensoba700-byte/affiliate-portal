const puppeteer = require('puppeteer');

(async () => {
  const asin = process.argv[2];
  if (!asin) {
    console.log(JSON.stringify({ error: "No ASIN provided" }));
    process.exit(1);
  }

  const browser = await puppeteer.launch({
    headless: true,
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });
  
  try {
    const page = await browser.newPage();
    await page.setUserAgent('Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/120.0.0.0');
    
    const url = `https://www.amazon.co.jp/dp/${asin}`;
    await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 30000 });
    
    // 等の描画されるのを少し待つ
    await new Promise(r => setTimeout(r, 3000));
    
    const data = await page.evaluate(() => {
      const titleEl = document.querySelector('#productTitle');
      const title = titleEl ? titleEl.textContent.trim() : '';
      
      let price = '';
      const priceWhole = document.querySelector('.a-price-whole');
      if (priceWhole) {
        price = priceWhole.textContent.trim();
      } else {
        const apexPrice = document.querySelector('.apexPriceToPay .a-offscreen');
        if (apexPrice) {
          price = apexPrice.textContent.trim();
        } else {
          const priceBlock = document.querySelector('#priceblock_ourprice');
          if (priceBlock) {
            price = priceBlock.textContent.trim();
          }
        }
      }

      const imgEl = document.querySelector('#landingImage') || document.querySelector('#imgBlkFront') || document.querySelector('#mainImageContainer img');
      const imageUrl = imgEl ? (imgEl.getAttribute('data-old-hires') || imgEl.getAttribute('src') || '') : '';

      return { title, price, imageUrl };
    });
    
    console.log(JSON.stringify(data));
  } catch (e) {
    console.log(JSON.stringify({ error: e.message }));
  } finally {
    await browser.close();
  }
})();
