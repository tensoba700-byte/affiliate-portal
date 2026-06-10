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

  // お勧め商品の本物画像をマークダウンから動的に取得
  let duoImage = '';
  let mujiImage = '';
  try {
    const balmArticle = await getArticleBySlug('20260609-cleansing-balm');
    const tonerArticle = await getArticleBySlug('20260608-toner');

    duoImage = balmArticle?.rankings?.find(p => p.name.includes('DUO'))?.imageUrl || '';
    mujiImage = tonerArticle?.rankings?.find(p => p.name.includes('無印良品'))?.imageUrl || '';
  } catch (error) {
    console.error("Failed to fetch recommended product images:", error);
  }

  return (
    <HomeClient 
      initialArticles={recentArticles} 
      duoImageUrl={duoImage} 
      mujiImageUrl={mujiImage} 
    />
  );
}

