import sys
import os

# プロジェクトのルートをパスに追加
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.prepare_stockpile import fetch_amazon_details_puppeteer

# Yunth VC Sheet Mask ASIN
asin = "B0GVGYFXDF"

print(f"Testing fetch_amazon_details_puppeteer for ASIN: {asin}...")
result = fetch_amazon_details_puppeteer(asin)
print("Result:")
print(result)
