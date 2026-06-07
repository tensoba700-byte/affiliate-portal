"use client";
import { useState } from "react";
import Link from "next/link";
import SearchBar from "@/src/components/SearchBar";

const categories = [
  { id: '1', name: 'Beauty & Skincare', jp: '美容・スキンケア', query: '美容' },
  { id: '2', name: 'Tech & Gadgets', jp: 'ガジェット', query: 'ガジェット' },
  { id: '3', name: 'Interior', jp: 'インテリア', query: 'インテリア' },
  { id: '4', name: 'Daily Goods', jp: '生活雑貨', query: '生活雑貨' },
  { id: '5', name: 'Useful Goods', jp: '便利グッズ', query: '便利グッズ' },
];

export default function Header() {
  const [open, setOpen] = useState(false);

  const toggleMenu = () => setOpen(!open);

  return (
    <header className="sticky top-0 z-50 w-full cute-glass">
      {/* Desktop Header */}
      <div className="container mx-auto px-4 h-16 flex items-center justify-between hidden md:flex">
        <Link href="/" className="text-2xl font-black tracking-tight text-primary flex items-center gap-1 hover:opacity-80 transition-opacity animate-float">
          みっけ！
        </Link>
        <div className="flex-1 max-w-lg mx-12">
          <SearchBar />
        </div>
        <nav className="flex items-center gap-8 text-sm font-bold">
          <Link href="/" className="text-muted hover:text-primary transition-colors">ホーム</Link>
          <Link href="/articles" className="text-muted hover:text-primary transition-colors">すべての記事</Link>
          <Link href="/articles" className="px-6 py-2.5 rounded-full bg-primary text-white hover:bg-primary/90 transition-all duration-300 shadow-md hover:cute-shadow hover:-translate-y-0.5">
            見つける
          </Link>
        </nav>
      </div>

      {/* Mobile Header */}
      <div className="flex items-center justify-between md:hidden px-4 h-16">
        <button onClick={toggleMenu} className="text-foreground/80 hover:text-primary transition-colors p-1" aria-label="メニュー">
          <svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
            <line x1="4" y1="12" x2="20" y2="12" />
            <line x1="4" y1="6" x2="20" y2="6" />
            <line x1="4" y1="18" x2="20" y2="18" />
          </svg>
        </button>
        
        <Link href="/" className="flex flex-col items-center hover:opacity-85 transition-opacity">
          <span className="text-2xl font-black tracking-tight text-foreground leading-none">みっけ！</span>
          <span className="text-[9px] font-bold text-muted tracking-widest leading-none mt-1 uppercase">mikke!</span>
        </Link>

        <Link href="/search" className="text-foreground/80 hover:text-primary transition-colors p-1" aria-label="検索">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
            <circle cx="11" cy="11" r="8" />
            <line x1="21" y1="21" x2="16.65" y2="16.65" />
          </svg>
        </Link>
      </div>

      {/* Mobile Search Bar (removed to match clean minimal layout) */}

      {/* Mobile Menu Overlay */}
      {open && (
        <div className="fixed inset-0 bg-black/60 z-40" onClick={toggleMenu} />
      )}
      <div className={`fixed inset-y-0 left-0 w-72 bg-white shadow-2xl transform ${open ? 'translate-x-0' : '-translate-x-full'} transition-transform duration-300 z-50`}>
        <div className="flex items-center justify-between p-6 border-b border-primary/5">
          <span className="text-xl font-black text-primary">
            メニュー <span className="theme-emoji-sweet">🌷</span><span className="theme-emoji-science font-mono select-none">✦</span>
          </span>
          <button onClick={toggleMenu} aria-label="閉じる" className="text-primary p-2 hover:bg-primary/5 rounded-full transition-colors">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round">
              <line x1="18" y1="6" x2="6" y2="18" />
              <line x1="6" y1="6" x2="18" y2="18" />
            </svg>
          </button>
        </div>
        <nav className="flex flex-col p-6 space-y-4">
          <Link href="/" className="text-base font-black text-foreground hover:text-primary transition-colors flex items-center gap-2" onClick={toggleMenu}>
            <span className="theme-emoji-sweet">🏠</span><span className="theme-emoji-science font-mono select-none">✦</span> ホーム
          </Link>
          <Link href="/articles" className="text-base font-black text-foreground hover:text-primary transition-colors flex items-center gap-2" onClick={toggleMenu}>
            <span className="theme-emoji-sweet">📚</span><span className="theme-emoji-science font-mono select-none">✦</span> すべての記事
          </Link>
          <div className="pt-4 pb-2">
            <p className="text-[10px] font-black text-muted tracking-widest uppercase mb-4">カテゴリー</p>
            <div className="flex flex-col space-y-3">
              {categories.map((cat) => (
                <Link
                  key={cat.id}
                  href={`/search?category=${encodeURIComponent(cat.jp)}`}
                  className="text-sm font-bold text-muted hover:text-primary transition-colors flex items-center gap-3 pl-2"
                  onClick={toggleMenu}
                >
                  <span className="w-1.5 h-1.5 rounded-full bg-primary/30"></span>
                  {cat.jp}
                </Link>
              ))}
            </div>
          </div>
        </nav>
      </div>
    </header>
  );
}
