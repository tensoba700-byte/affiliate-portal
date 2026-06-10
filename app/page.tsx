import React from 'react';
import { getAllArticles, getArticleBySlug, ArticleItem } from '@/src/lib/api';
import HomeClient from '@/src/components/HomeClient';
import type { Metadata } from 'next';

export const metadata: Metadata = {
  alternates: {
    canonical: '/',
  },
};

export default async function Home() {
  let recentArticles: ArticleItem[] = [];
  let balmArticle: ArticleItem | undefined;
  let tonerArticle: ArticleItem | undefined;
  try {
    const articles = await getAllArticles();
    recentArticles = articles.slice(0, 6);
    
    // 最新記事からクレンジングバーム・化粧水に合致するものを動的検索
    balmArticle = articles.find(a => a.slug.includes('cleansing-balm') || a.title.includes('クレンジングバーム'));
    tonerArticle = articles.find(a => a.slug.includes('toner') || a.title.includes('化粧水'));
  } catch (error) {
    console.error("Failed to fetch articles:", error);
  }

  // お勧め商品の本物画像 & Amazon URLをマークダウンから動的に取得
  let duoImage = '';
  let mujiImage = '';
  let duoAmazonUrl = '';
  let mujiAmazonUrl = '';
  let duoSlug = '';
  let mujiSlug = '';
  let duoTitle = '';
  let mujiTitle = '';
  let duoPrice = '';
  let mujiPrice = '';
  let duoRating = '';
  let mujiRating = '';

  try {
    // もし最新順の検索で見つからなかった場合のフォールバック
    const actualBalm = balmArticle || await getArticleBySlug('20260609-cleansing-balm');
    const actualToner = tonerArticle || await getArticleBySlug('20260608-toner');

    const duoProd = actualBalm?.rankings?.find(p => p.name.includes('DUO'));
    const mujiProd = actualToner?.rankings?.find(p => p.name.includes('無印良品'));

    duoImage = duoProd?.imageUrl || '';
    duoAmazonUrl = duoProd?.amazon?.url || '';
    duoSlug = actualBalm?.slug || '20260609-cleansing-balm';
    duoTitle = actualBalm?.title || '最強クレンジングバーム7選';

    const dp = duoProd?.amazon?.price || duoProd?.yahoo?.price || duoProd?.rakuten?.price;
    duoPrice = dp ? (dp.startsWith('¥') ? dp : `¥${dp}`) : '¥3,960';
    duoRating = duoProd?.score ? duoProd.score.toFixed(1) : '4.8';

    mujiImage = mujiProd?.imageUrl || '';
    mujiAmazonUrl = mujiProd?.amazon?.url || '';
    mujiSlug = actualToner?.slug || '20260608-toner';
    mujiTitle = actualToner?.title || 'プチプラ実力派化粧水6選';

    const mp = mujiProd?.amazon?.price || mujiProd?.yahoo?.price || mujiProd?.rakuten?.price;
    mujiPrice = mp ? (mp.startsWith('¥') ? mp : `¥${mp}`) : '¥1,290';
    mujiRating = mujiProd?.score ? mujiProd.score.toFixed(1) : '4.7';

  } catch (error) {
    console.error("Failed to fetch recommended product details:", error);
  }

  return (
    <HomeClient 
      initialArticles={recentArticles} 
      duoImageUrl={duoImage} 
      mujiImageUrl={mujiImage} 
      duoAmazonUrl={duoAmazonUrl}
      mujiAmazonUrl={mujiAmazonUrl}
      duoSlug={duoSlug}
      mujiSlug={mujiSlug}
      duoTitle={duoTitle}
      mujiTitle={mujiTitle}
      duoPrice={duoPrice}
      mujiPrice={mujiPrice}
      duoRating={duoRating}
      mujiRating={mujiRating}
    />
  );
}

