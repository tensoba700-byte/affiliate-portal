import React from 'react';
import Link from 'next/link';

export default function SampleHeader() {
  return (
    <header className="sample-header">
      <div className="sample-header-inner">
        {/* Left: tagline */}
        <span className="sample-header-tagline">本音コスメ検証メディア</span>

        {/* Center Logo & Nav */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 24 }}>
          <Link href="/sample" className="sample-logo">
            mikke!
          </Link>
          <nav style={{ display: 'flex', gap: 16 }}>
            <Link href="/sample/products" style={{ fontSize: 10, fontWeight: 800, letterSpacing: '0.06em', color: 'var(--s-ink)', textDecoration: 'none', textTransform: 'uppercase' }}>Products</Link>
            <Link href="/sample/column" style={{ fontSize: 10, fontWeight: 800, letterSpacing: '0.06em', color: 'var(--s-ink)', textDecoration: 'none', textTransform: 'uppercase' }}>Journal</Link>
          </nav>
        </div>

        {/* Right Icons */}
        <div className="sample-header-actions">
          <button className="sample-icon-btn" aria-label="検索">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <circle cx="11" cy="11" r="8" /><line x1="21" y1="21" x2="16.65" y2="16.65" />
            </svg>
          </button>

        </div>
      </div>
    </header>
  );
}
