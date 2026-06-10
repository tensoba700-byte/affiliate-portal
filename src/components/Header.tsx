"use client";

import React, { useState } from 'react';
import Link from 'next/link';
import SearchBar from "@/src/components/SearchBar";

export default function Header() {
  const [isMenuOpen, setIsMenuOpen] = useState(false);

  return (
    <header className="sample-header">
      <div className="sample-header-inner">
        {/* Left: tagline */}
        <span className="sample-header-tagline">本音コスメ検証メディア</span>

        {/* Center Logo & Nav */}
        <div className="sample-header-center">
          <Link href="/" className="sample-logo">
            mikke!
          </Link>
          <nav className="sample-desktop-nav">
            <Link href="/articles" className="sample-nav-item">記事一覧</Link>
            <Link href="/products" className="sample-nav-item">商品一覧</Link>
            <Link href="/column" className="sample-nav-item">美容コラム</Link>
          </nav>
        </div>

        {/* Right Icons */}
        <div className="sample-header-actions" style={{ gap: '12px' }}>
          {/* Desktop Search Bar */}
          <div className="hidden md:block" style={{ width: '200px' }}>
            <SearchBar />
          </div>

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

      {/* Mobile Search Bar */}
      <div className="block md:hidden px-4 pb-3" style={{ background: 'rgba(250, 250, 248, 0.92)' }}>
        <SearchBar />
      </div>

      {/* Mobile Dropdown Menu */}
      {isMenuOpen && (
        <nav className="sample-mobile-nav" style={{ top: '102px' }}>
          <div className="sample-mobile-nav-inner">
            <div className="sample-mobile-menu-section">
              <Link href="/articles" className="sample-mobile-nav-item" onClick={() => setIsMenuOpen(false)}>
                記事一覧
              </Link>
              <Link href="/products" className="sample-mobile-nav-item" onClick={() => setIsMenuOpen(false)}>
                商品一覧
              </Link>
              <Link href="/column" className="sample-mobile-nav-item" onClick={() => setIsMenuOpen(false)}>
                美容コラム
              </Link>
            </div>

            <div className="sample-mobile-cat-section">
              <div className="sample-mobile-cat-title">CATEGORIES</div>
              <div className="sample-mobile-cat-list">
                <Link href="/products" className="sample-mobile-cat-item" onClick={() => setIsMenuOpen(false)}>
                  美容・スキンケア
                </Link>
                <span className="sample-mobile-cat-item-coming">ガジェット</span>
                <span className="sample-mobile-cat-item-coming">インテリア</span>
                <span className="sample-mobile-cat-item-coming">生活雑貨</span>
                <span className="sample-mobile-cat-item-coming">便利グッズ</span>
              </div>
            </div>
          </div>
        </nav>
      )}
    </header>
  );
}

