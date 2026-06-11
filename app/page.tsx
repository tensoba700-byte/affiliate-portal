import React from 'react';
import { getAllArticles, ArticleItem } from '@/src/lib/api';
import HomeClient from '@/src/components/HomeClient';
import type { Metadata } from 'next';

export const metadata: Metadata = {
  alternates: {
    canonical: '/',
  },
};

export interface PickItem {
  id: string;
  name: string;
  price: string;
  rating: string;
  type: string;
  articleSlug: string;
  articleLabel: string;
  imageUrl: string;
  amazonUrl: string;
}

export default async function Home() {
  let recentArticles: ArticleItem[] = [];
  let picks: PickItem[] = [];

  try {
    const articles = await getAllArticles();
    recentArticles = articles.slice(0, 6);

    // rankingsが存在する最新の最大4記事を取得
    const targetArticles = articles.filter(a => a.rankings && a.rankings.length > 0).slice(0, 4);

    picks = targetArticles.map((article, index) => {
      const firstProd = article.rankings.find(p => p.rank === 1) || article.rankings[0];
      
      const priceVal = firstProd.amazon?.price || firstProd.yahoo?.price || firstProd.rakuten?.price || 'なし';
      let formattedPrice = '価格を見る';
      if (priceVal && priceVal !== 'なし') {
        const cleaned = priceVal.replace(/円/g, '').replace(/,/g, '').trim();
        if (/^\d+$/.test(cleaned)) {
          formattedPrice = `¥${parseInt(cleaned, 10).toLocaleString()}`;
        } else {
          formattedPrice = priceVal.startsWith('¥') ? priceVal : `¥${priceVal}`;
        }
      }

      const cat = article.category || '';
      let type = 'ITEM';
      if (cat.includes('バーム')) type = 'BALM';
      else if (cat.includes('化粧水')) type = 'TONER';
      else if (cat.includes('美容液') || cat.includes('導入')) type = 'SERUM';
      else if (cat.includes('ジェル')) type = 'GEL';
      else if (cat.includes('クレンジング')) type = 'CLEANSING';
      else if (cat.includes('オイル')) type = 'OIL';
      else if (cat.includes('パック') || cat.includes('マスク')) type = 'MASK';
      else if (cat.includes('ガジェット')) type = 'GADGET';
      else if (cat.includes('生活雑貨') || cat.includes('便利グッズ')) type = 'GOODS';

      return {
        id: firstProd.name || `pick_${index}`,
        name: firstProd.name || 'おすすめ商品',
        price: formattedPrice,
        rating: firstProd.score ? firstProd.score.toFixed(1) : '4.5',
        type: type,
        articleSlug: article.slug,
        articleLabel: article.title.replace(/<br\s*\/?>/gi, ' '),
        imageUrl: firstProd.imageUrl || '',
        amazonUrl: firstProd.amazon?.url || '',
      };
    });
  } catch (error) {
    console.error("Failed to fetch articles or picks:", error);
  }

  return (
    <HomeClient 
      initialArticles={recentArticles} 
      picks={picks}
    />
  );
}

