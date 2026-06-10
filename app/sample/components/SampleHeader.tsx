import React from 'react';
import Link from 'next/link';

export default function SampleHeader() {
  return (
    <header className="sample-header">
      <div className="sample-header-inner">
        {/* Left: tagline */}
        <span className="sample-header-tagline">本音コスメ検証メディア</span>

        {/* Center Logo */}
        <Link href="/sample" className="sample-logo">
          mikke!
        </Link>

        {/* Right Icons */}
        <div className="sample-header-actions">
          <button className="sample-icon-btn" aria-label="検索">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <circle cx="11" cy="11" r="8" /><line x1="21" y1="21" x2="16.65" y2="16.65" />
            </svg>
          </button>
          <button className="sample-icon-btn" aria-label="マイページ">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" /><circle cx="12" cy="7" r="4" />
            </svg>
          </button>
        </div>
      </div>
    </header>
  );
}
