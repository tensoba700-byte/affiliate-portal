"use client";

import React, { useState } from 'react';
import Link from 'next/link';

export default function SampleHeader() {
  const [isMenuOpen, setIsMenuOpen] = useState(false);

  return (
    <header className="sample-header">
      <div className="sample-header-inner">
        {/* Left: tagline */}
        <span className="sample-header-tagline">本音コスメ検証メディア</span>

        {/* Center Logo & Nav */}
        <div className="sample-header-center">
          <Link href="/sample" className="sample-logo">
            mikke!
          </Link>
          <nav className="sample-desktop-nav">
            <Link href="/sample/articles" className="sample-nav-item">記事一覧</Link>
            <Link href="/sample/products" className="sample-nav-item">商品一覧</Link>
            <Link href="/sample/column" className="sample-nav-item">美容コラム</Link>
          </nav>
        </div>

        {/* Right Icons & Hamburger */}
        <div className="sample-header-actions">
          <button className="sample-icon-btn" aria-label="検索">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <circle cx="11" cy="11" r="8" /><line x1="21" y1="21" x2="16.65" y2="16.65" />
            </svg>
          </button>

          <button 
            className="sample-menu-toggle" 
            aria-label="メニューを開閉"
            onClick={() => setIsMenuOpen(!isMenuOpen)}
            aria-expanded={isMenuOpen}
          >
            {isMenuOpen ? (
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <line x1="18" y1="6" x2="6" y2="18"></line>
                <line x1="6" y1="6" x2="18" y2="18"></line>
              </svg>
            ) : (
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <line x1="3" y1="12" x2="21" y2="12"></line>
                <line x1="3" y1="6" x2="21" y2="6"></line>
                <line x1="3" y1="18" x2="21" y2="18"></line>
              </svg>
            )}
          </button>
        </div>
      </div>

      {/* Mobile Dropdown Menu */}
      {isMenuOpen && (
        <nav className="sample-mobile-nav">
          <div className="sample-mobile-nav-inner">
            <Link href="/sample/articles" className="sample-mobile-nav-item" onClick={() => setIsMenuOpen(false)}>
              記事一覧
            </Link>
            <Link href="/sample/products" className="sample-mobile-nav-item" onClick={() => setIsMenuOpen(false)}>
              商品一覧
            </Link>
            <Link href="/sample/column" className="sample-mobile-nav-item" onClick={() => setIsMenuOpen(false)}>
              美容コラム
            </Link>
          </div>
        </nav>
      )}
    </header>
  );
}

