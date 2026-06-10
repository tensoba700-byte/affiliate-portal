import React from 'react';
import { getAllArticles, ArticleItem } from '@/src/lib/api';
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


  return <HomeClient initialArticles={recentArticles} />;
}

