// src/lib/affiliateHelpers.ts

/**
 * Helper functions to generate affiliate URLs for Amazon and Rakuten.
 */

export const amazonUrl = (asin: string): string => {
  return `https://www.amazon.co.jp/dp/${asin}`;
};

export const amazonSearchUrl = (query: string): string => {
  return `https://www.amazon.co.jp/s?k=${encodeURIComponent(query)}`;
};

export const rakutenUrl = (originalUrl: string): string => {
  return originalUrl;
};
