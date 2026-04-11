// src/lib/affiliateHelpers.ts

/**
 * Helper functions to generate affiliate URLs for Amazon and Rakuten.
 * If a full URL is passed (starts with http), it is returned as-is.
 */

export const amazonUrl = (asinOrUrl: string): string => {
  // If a full affiliate URL is passed, use it directly
  if (asinOrUrl.startsWith('http')) return asinOrUrl;
  return `https://www.amazon.co.jp/dp/${asinOrUrl}`;
};

export const amazonSearchUrl = (query: string): string => {
  return `https://www.amazon.co.jp/s?k=${encodeURIComponent(query)}`;
};

export const rakutenUrl = (originalUrl: string): string => {
  return originalUrl;
};
