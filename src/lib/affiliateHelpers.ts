// src/lib/affiliateHelpers.ts

/**
 * Helper functions to generate affiliate URLs for Amazon and Rakuten.
 */

export const amazonUrl = (asin: string): string => {
  const tag = process.env.AMAZON_ASSOCIATE_TAG || 'mikkestyle-22';
  return `https://www.amazon.co.jp/dp/${asin}?tag=${tag}`;
};

export const amazonSearchUrl = (query: string): string => {
  const tag = process.env.AMAZON_ASSOCIATE_TAG || 'mikkestyle-22';
  return `https://www.amazon.co.jp/s?k=${encodeURIComponent(query)}&tag=${tag}`;
};

export const rakutenUrl = (originalUrl: string): string => {
  const id = process.env.RAKUTEN_AFFILIATE_ID || '52aa350c.c59bcb5a.52aa350d.c841a8ec';
  const encoded = encodeURIComponent(originalUrl);
  return `https://hb.afl.rakuten.co.jp/ichiba/${id}/?pc=${encoded}&m=${encoded}`;
};
