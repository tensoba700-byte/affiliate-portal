"use client";

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { ArticleItem } from '@/src/lib/api';

interface HomeClientProps {
  initialArticles: ArticleItem[];
  duoImageUrl?: string;
  mujiImageUrl?: string;
}

export default function HomeClient({ initialArticles, duoImageUrl, mujiImageUrl }: HomeClientProps) {
  const images = [
    '/images/sample_hero_bg.png',
    '/images/hero_flatlay_marble.png',
    '/images/hero_flatlay_linen.png',
    '/images/hero_flatlay_lifestyle.png',
    '/images/hero_flatlay_cream.png'
  ];

  const copies = [
    'お気に入りを、みっけ。',
    'お気に入りを、mikke!'
  ];

  const [heroBg, setHeroBg] = useState('/images/sample_hero_bg.png');
  const [heroTitle, setHeroTitle] = useState('お気に入りを、みっけ。');

  useEffect(() => {
    const randomIndex = Math.floor(Math.random() * images.length);
    setHeroBg(images[randomIndex]);

    const randomCopyIndex = Math.floor(Math.random() * copies.length);
    setHeroTitle(copies[randomCopyIndex]);
  }, []);

  // 本物の最新記事データをサンプルカードのフォーマットにマッピング
  const latestArticles = initialArticles.map((article) => {
    let dateStr = '2026.06.09';
    if (article.publishedAt) {
      const d = new Date(article.publishedAt);
      if (!isNaN(d.getTime())) {
        dateStr = d.toLocaleDateString('ja-JP').replace(/\//g, '.');
      }
    }

    return {
      slug: article.slug,
      title: article.title,
      excerpt: article.excerpt || '大人気コスメを本音でガチ検証レビュー！メイク落ちや使用感を徹底的に解説するよ。',
      date: dateStr,
      category: '美容・スキンケア',
      image: article.coverImage || '/eyecatch/20260609-cleansing-balm-sample.png'
    };
  });

  const latestColumns = [
    {
      slug: 'night-pore-reset',
      title: '仕事帰りの10分でできる！夕方の毛穴に絶望しないための夜のリセット習慣',
      date: '2026.06.09',
      category: 'ESSAY',
      image: '/images/column_night_pore_reset.png'
    },
    {
      slug: 'honest-makeup-base',
      title: 'コスメオタク美容ライターの本音。本当に「夕方ににじまない」メイク下地の選び方',
      date: '2026.06.08',
      category: 'BEAUTY TIPS',
      image: '/images/column_makeup_base.png'
    }
  ];

  const recommendedItems = [
    {
      id: '1',
      name: 'DUO ザ クレンジングバーム',
      price: '¥3,960',
      rating: '4.8',
      type: 'BALM',
      articleSlug: '20260609-cleansing-balm',
      articleLabel: '最強クレンジングバーム7選',
      imageUrl: duoImageUrl
    },
    {
      id: '2',
      name: '無印良品 敏感肌用化粧水',
      price: '¥1,290',
      rating: '4.7',
      type: 'TONER',
      articleSlug: '20260608-toner',
      articleLabel: 'プチプラ実力派化粧水6選',
      imageUrl: mujiImageUrl
    }
  ];

  return (
    <div className="s-home-wrapper">
      {/* ── Hero Banner ── */}
      <div className="s-hero">
        <div
          className="s-hero-image-wrap"
          style={{
            backgroundImage: `url("${heroBg}")`
          }}
        >
          <div className="s-hero-overlay" />
          <div className="s-hero-panel">
            <div className="s-hero-eyebrow">
              <span className="s-badge-primary">FEATURE</span>
              <span className="s-badge-ghost">EDITORIAL EDITION</span>
            </div>
            <h1 className="s-hero-title">
              {heroTitle}
            </h1>
            <p className="s-hero-desc">
              美容・ガジェット・インテリア。暮らしをちょっとよくするアイテムを
            </p>
          </div>
        </div>
      </div>

      {/* ── Category Nav ── */}
      <nav className="s-cat-nav" aria-label="カテゴリーナビ">
        <div className="s-cat-nav-inner">
          <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
            <Link href="/" className="s-nav-link-active">ホーム</Link>
            <Link href="/articles" className="s-nav-link">記事一覧</Link>
            <Link href="/products" className="s-nav-link">商品一覧</Link>
            <Link href="/column" className="s-nav-link">美容コラム</Link>
          </div>
          <span className="s-nav-divider">|</span>
          <span className="s-nav-tag">CATEGORY:</span>
          <span className="s-nav-coming">美容・スキンケア</span>
          <span className="s-nav-coming">ガジェット</span>
          <span className="s-nav-coming">インテリア</span>
          <span className="s-nav-coming">生活雑貨</span>
          <span className="s-nav-coming">便利グッズ</span>
        </div>
      </nav>

      {/* ── Main Content ── */}
      <div className="s-main">

        {/* ── Recommended Items ── */}
        <section>
          <div className="s-section-head">
            <div>
              <div className="s-section-label">PICKS</div>
              <div className="s-section-sub">おすすめアイテム</div>
            </div>
            <Link href="/products" className="s-section-link">LAB PICK →</Link>
          </div>

          <div className="s-items-scroll">
            {recommendedItems.map((prod) => (
              <div key={prod.id} className="s-item-card">
                <div className="s-item-img">
                  {prod.imageUrl ? (
                    <img 
                      src={prod.imageUrl} 
                      alt={prod.name} 
                      style={{ 
                        width: '100%', 
                        height: '100%', 
                        objectFit: 'contain',
                        mixBlendMode: 'multiply'
                      }} 
                      referrerPolicy="no-referrer"
                    />
                  ) : (
                    <div style={{
                      width: 40, height: 72,
                      border: '1px solid #d6d3d1',
                      borderRadius: 6,
                      background: '#fafaf8',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      position: 'relative',
                    }}>
                      <div style={{
                        position: 'absolute', top: -5, left: '50%', transform: 'translateX(-50%)',
                        width: 18, height: 8,
                        background: '#1C1917', borderRadius: 3
                      }} />
                      <span className="s-item-type" style={{ writingMode: 'vertical-rl' }}>{prod.type}</span>
                    </div>
                  )}
                </div>
                <div>
                  <p className="s-item-name">{prod.name}</p>
                  <div className="s-item-meta">
                    <span className="s-item-price">{prod.price}</span>
                    <span className="s-item-rating">⭐ {prod.rating}</span>
                  </div>
                  {prod.articleSlug && (
                    <Link
                      href={`/articles/${prod.articleSlug}`}
                      className="s-article-link-btn"
                      style={{ marginTop: 12 }}
                    >
                      📄 この記事で紹介！
                    </Link>
                  )}
                </div>
              </div>
            ))}
          </div>
        </section>

        {/* ── Latest Articles ── */}
        <section>
          <div className="s-section-head">
            <div>
              <div className="s-section-label">LATEST VERIFICATIONS</div>
              <div className="s-section-sub">編集部が体を張って検証した本音レポート</div>
            </div>
            <Link href="/articles" className="s-section-link">NEW REPORTS →</Link>
          </div>

          <div className="s-article-grid">
            {latestArticles.map((article) => (
              <Link
                key={article.slug}
                href={`/articles/${article.slug}`}
                className="s-article-card"
              >
                <div className="s-article-thumb">
                  <img 
                    src={article.image} 
                    alt={article.title} 
                    className="s-article-img"
                    loading="lazy"
                  />
                  <span className="s-article-thumb-badge">NEW REPORT</span>
                </div>
                <div className="s-article-body">
                  <span className="s-article-date">{article.date}</span>
                  <h3 className="s-article-title">{article.title}</h3>
                  <p className="s-article-excerpt">{article.excerpt}</p>
                  <div className="s-article-read-more">
                    READ REPORT <span>→</span>
                  </div>
                </div>
              </Link>
            ))}
          </div>
        </section>

        {/* ── Beauty Column ── */}
        <section>
          <div className="s-section-head">
            <div>
              <div className="s-section-label">BEAUTY COLUMN</div>
              <div className="s-section-sub">美容オタクライターが綴るお肌のエッセイ</div>
            </div>
            <Link href="/column" className="s-section-link">VIEW JOURNAL →</Link>
          </div>

          <div className="s-column-list">
            {latestColumns.map((col) => (
              <Link
                key={col.slug}
                href={`/column/${col.slug}`}
                className="s-column-card"
                style={{ backgroundImage: `url(${col.image})` }}
              >
                <div style={{ flex: 1 }}>
                  <span className="s-column-cat">{col.category}</span>
                  <p className="s-column-title">{col.title}</p>
                </div>
                <span className="s-column-date">{col.date}</span>
                <span className="s-column-arrow">→</span>
              </Link>
            ))}
          </div>
        </section>

        {/* ── Background Blend Demo ── */}
        <section className="s-demo-box">
          <div className="s-section-head" style={{ marginBottom: 0 }}>
            <div>
              <div className="s-section-label">BACKGROUND BLEND DEMO</div>
              <div className="s-section-sub">ECサイトの白背景画像をグレー背景に溶け込ませるデモ</div>
            </div>
            <span className="s-section-link">LAB DEMO</span>
          </div>

          <div className="s-demo-grid">
            <div className="s-demo-card">
              <span className="s-demo-label s-demo-label-light">元の画像（白背景）</span>
              <div className="s-demo-img-wrap" style={{ background: '#f5f5f4', border: '1px solid #e7e5e4' }}>
                <img
                  src="https://images.unsplash.com/photo-1601049541289-9b1b7bbbfe19?w=400&q=80"
                  alt="Original White Background Product"
                  style={{ height: '100%', objectFit: 'contain' }}
                />
              </div>
              <p className="s-demo-desc">ECサイトによくある典型的な白背景の商品画像</p>
            </div>

            <div className="s-demo-card">
              <span className="s-demo-label s-demo-label-dark">CSS乗算後（グレーに馴染む）</span>
              <div
                className="s-demo-img-wrap"
                style={{
                  background: '#f4f4f5',
                  backgroundImage: 'radial-gradient(circle, rgba(28,25,23,0.03) 0%, rgba(28,25,23,0.08) 100%)'
                }}
              >
                <img
                  src="https://images.unsplash.com/photo-1601049541289-9b1b7bbbfe19?w=400&q=80"
                  alt="Blended Product"
                  style={{ height: '100%', objectFit: 'contain', mixBlendMode: 'multiply' }}
                />
              </div>
              <p className="s-demo-desc">CSS乗算を使うと、白背景が消えてグレー背景に自然に馴染むよ！</p>
            </div>
          </div>
        </section>

      </div>
    </div>
  );
}
