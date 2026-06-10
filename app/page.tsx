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
  try {
    const articles = await getAllArticles();
    recentArticles = articles.slice(0, 6);
  } catch (error) {
    console.error("Failed to fetch articles:", error);
  }

  // お勧め商品の本物画像 & Amazon URLをマークダウンから動的に取得
  let duoImage = '';
  let mujiImage = '';
  let duoAmazonUrl = '';
  let mujiAmazonUrl = '';
  try {
    const balmArticle = await getArticleBySlug('20260609-cleansing-balm');
    const tonerArticle = await getArticleBySlug('20260608-toner');

    const duoProd = balmArticle?.rankings?.find(p => p.name.includes('DUO'));
    const mujiProd = tonerArticle?.rankings?.find(p => p.name.includes('無印良品'));

    duoImage = duoProd?.imageUrl || '';
    duoAmazonUrl = duoProd?.amazon?.url || '';

    mujiImage = mujiProd?.imageUrl || '';
    mujiAmazonUrl = mujiProd?.amazon?.url || '';
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
    />
  );
}

