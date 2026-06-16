import subprocess
import tempfile
import os

asin = "B0GVGYFXDF"

js_code = r"""
const puppeteer = require('puppeteer');
(async () => {
  console.log("Launching browser...");
  try {
    const browser = await puppeteer.launch({
      headless: true,
      args: ['--no-sandbox', '--disable-setuid-sandbox']
    });
    console.log("Browser launched.");
    const page = await browser.newPage();
    await page.setUserAgent('Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/120.0.0.0');
    
    const asin = process.argv[2];
    const url = `https://www.amazon.co.jp/dp/${asin}`;
    console.log(`Going to ${url}...`);
    await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 30000 });
    console.log("Page loaded.");
    
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
      return { title, price };
    });
    console.log("Evaluation complete:", JSON.stringify(data));
    await browser.close();
  } catch (e) {
    console.error("Error in Puppeteer:", e);
  }
})();
"""

with tempfile.NamedTemporaryFile(mode='w', suffix='.js', delete=False, encoding='utf-8') as f:
    f.write(js_code)
    temp_js = f.name

try:
    print("Running node command...")
    res = subprocess.run(
        ["node", temp_js, asin],
        capture_output=True, text=True, timeout=45
    )
    print("Return code:", res.returncode)
    print("STDOUT:")
    print(res.stdout)
    print("STDERR:")
    print(res.stderr)
finally:
    try:
        os.unlink(temp_js)
    except Exception:
        pass
