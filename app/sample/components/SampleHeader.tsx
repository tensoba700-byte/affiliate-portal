import React from 'react';
import Link from 'next/link';

interface SampleHeaderProps {
  currentTheme?: 'clean-science' | 'korean-cafe';
  onToggleTheme?: () => void;
}

export default function SampleHeader({ currentTheme, onToggleTheme }: SampleHeaderProps) {
  return (
    <header className="w-full bg-white border-b border-card-border sticky top-0 z-50 transition-all duration-300">
      <div className="container mx-auto max-w-4xl px-4 h-14 flex items-center justify-between">
        {/* Left Area - Theme Toggle Button */}
        <div className="flex items-center gap-2">
          {onToggleTheme && (
            <button 
              onClick={onToggleTheme}
              className="px-3 py-1.5 rounded-full text-[9px] font-black tracking-wider border border-card-border hover:bg-zinc-50 transition-all uppercase cursor-pointer flex items-center gap-1 active:scale-95"
            >
              {currentTheme === 'korean-cafe' ? (
                <>
                  <span className="text-[11px]">☕</span>
                  <span>Cafe Style</span>
                </>
              ) : (
                <>
                  <span className="text-[11px]">🔬</span>
                  <span>Science Style</span>
                </>
              )}
            </button>
          )}
        </div>

        {/* Center Logo */}
        <Link 
          href="/sample" 
          className={`text-xl font-black tracking-widest text-foreground transition-all duration-500 ${
            currentTheme === 'korean-cafe' ? 'font-serif lowercase normal-case tracking-normal' : 'font-mono uppercase'
          }`}
        >
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

