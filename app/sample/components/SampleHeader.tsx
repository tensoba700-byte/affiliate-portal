import React from 'react';
import Link from 'next/link';

export default function SampleHeader() {
  return (
    <header className="w-full bg-white border-b border-card-border sticky top-0 z-50 transition-all duration-300">
      <div className="container mx-auto max-w-4xl px-4 h-14 flex items-center justify-between">
        {/* Left Menu Button (Minimal) */}
        <button className="text-foreground p-1 hover:opacity-75 transition-opacity" aria-label="メニュー">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <line x1="4" y1="12" x2="20" y2="12" />
            <line x1="4" y1="6" x2="20" y2="6" />
            <line x1="4" y1="18" x2="20" y2="18" />
          </svg>
        </button>

        {/* Center Logo */}
        <Link href="/sample" className="text-xl font-black tracking-widest text-foreground font-mono">
          mikke!
        </Link>

        {/* Right Icons (Minimalist search/bag icons like high-end cosmetics e-commerce) */}
        <div className="flex items-center gap-3">
          <button className="text-foreground p-1 hover:opacity-75" aria-label="検索">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <circle cx="11" cy="11" r="8" /><line x1="21" y1="21" x2="16.65" y2="16.65" />
            </svg>
          </button>
          <button className="text-foreground p-1 hover:opacity-75" aria-label="マイページ">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" /><circle cx="12" cy="7" r="4" />
            </svg>
          </button>
        </div>
      </div>
    </header>
  );
}
