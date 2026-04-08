// src/lib/affiliateHelpers.ts

/**
 * Helper functions to generate affiliate URLs for Amazon and Rakuten.
 */

export const amazonUrl = (asin: string): string => {
  const tag = process.env.AMAZON_ASSOCIATE_TAG ?? '';
  return `https://www.amazon.co.jp/dp/${asin}/?tag=${tag}`;
};

export const rakutenUrl = (originalUrl: string): string => {
  const id = process.env.RAKUTEN_AFFILIATE_ID ?? '';
  const encoded = encodeURIComponent(originalUrl);
  return `https://hb.afl.rakuten.co.jp/ichiba/${id}/?pc=${encoded}&m=${encoded}`;
};
