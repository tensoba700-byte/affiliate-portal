import React from 'react';
import Link from 'next/link';
import { getAllArticles, ArticleItem } from '@/src/lib/api';
import { AdBanner } from '@/src/components/AdBanner';
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

  // Recommended products based on the clean science UI mock
  const recommendedProducts = [
    { id: 'p1', name: 'CLEANSE OIL', price: '¥1,300', rating: '4.5', image: '/images/prod_cleanse_oil.png' },
    { id: 'p2', name: 'MOIST LOTION', price: '¥1,500', rating: '4.5', image: '/images/prod_moist_lotion.png' },
    { id: 'p3', name: 'BALANCE TONER', price: '¥1,500', rating: '4.5', image: '/images/prod_balance_toner.png' },
  ];

  return (
    <div className="flex flex-col items-center w-full pb-24 overflow-x-hidden mt-[-64px]">
      
      {/* 💿 Concrete Hero Banner Section with overlapping header effect */}
      <section 
        className="w-full relative min-h-[42vh] md:min-h-[50vh] flex flex-col justify-end bg-cover bg-center px-6 pb-8 pt-24"
        style={{ backgroundImage: 'url("/images/hero_concrete.png")' }}
      >
        <div className="absolute inset-0 bg-black/5 mix-blend-multiply pointer-events-none"></div>
        
        {/* Subtle Overlay Text */}
        <div className="container mx-auto max-w-5xl z-10 text-white/90 drop-shadow-sm select-none pointer-events-none mb-4">
          <p className="text-[10px] md:text-xs font-mono font-bold tracking-[0.25em] uppercase text-white/70">
            MINIMALISM & SCIENCE
          </p>
          <h2 className="text-xl md:text-3xl font-bold tracking-[0.15em] mt-1 font-mono">
            INDUSTRIAL MINIMALISM
          </h2>
        </div>
      </section>

      {/* 🧭 Horizontal Category Navigation Bar */}
      <div className="w-full bg-[#d4d4d8]/90 backdrop-blur-md border-b border-zinc-300/40 sticky top-16 z-30 flex justify-center">
        <div className="container mx-auto max-w-5xl px-4 overflow-x-auto hide-scrollbar">
          <nav className="flex items-center space-x-6 md:space-x-12 py-3 text-[13px] md:text-[14px] font-bold text-zinc-900 whitespace-nowrap min-w-max">
            <Link href="/" className="border-b-2 border-white pb-1.5 transition-colors">ホーム</Link>
            <Link href="/articles" className="hover:opacity-70 pb-1.5 transition-opacity">特集</Link>
            <Link href="/articles" className="hover:opacity-70 pb-1.5 transition-opacity">アイテム</Link>
            <Link href="/articles" className="hover:opacity-70 pb-1.5 transition-opacity">コスメ</Link>
            <Link href="/articles" className="hover:opacity-70 pb-1.5 transition-opacity">ショップ</Link>
          </nav>
        </div>
      </div>

      {/* 🛡️ Content Wrapper */}
      <div className="container mx-auto max-w-5xl px-4 mt-8 md:mt-12 w-full space-y-12">

        {/* 📰 今月の特集 (Monthly Feature Banner) */}
        <section className="w-full">
          <h2 className="text-base md:text-lg font-bold text-zinc-800 tracking-wider mb-4 font-sans border-b border-zinc-300/50 pb-2">
            今月の特集：韓国ミニマルビューティー
          </h2>
          
          <div className="group relative overflow-hidden rounded-2xl border border-zinc-950/8 bg-white/70 backdrop-blur-md p-6 md:p-8 flex flex-row items-center justify-between gap-6 hover:border-zinc-950/15 hover:shadow-lg transition-all duration-300">
            {/* Left Content */}
            <div className="flex-1 flex flex-col justify-center">
              <h3 className="text-lg md:text-3xl font-bold text-zinc-900 tracking-tight leading-snug">
                透明感を引き出す、<br />
                究極のシンプルケア
              </h3>
              <div className="mt-6">
                <Link href="/articles" className="inline-flex items-center gap-1.5 text-xs font-mono font-bold tracking-widest text-zinc-500 group-hover:text-black transition-colors">
                  READ MORE <span className="text-sm">→</span>
                </Link>
              </div>
            </div>
            
            {/* Right Image */}
            <div className="w-24 h-24 sm:w-36 sm:h-36 md:w-48 md:h-48 rounded-xl overflow-hidden flex-shrink-0 bg-zinc-50">
              <img 
                src="/images/banner_skincare.png" 
                alt="韓国ミニマルビューティー" 
                loading="lazy"
                className="w-full h-full object-cover transition-transform duration-500 group-hover:scale-103"
              />
            </div>
          </div>
        </section>

        {/* 🧪 おすすめコスメ (Recommended Products Horizontal Scroll) */}
        <section className="w-full">
          <h2 className="text-base md:text-lg font-bold text-zinc-800 tracking-wider mb-4 font-sans border-b border-zinc-300/50 pb-2">
            おすすめコスメ
          </h2>
          
          <div className="flex gap-4 overflow-x-auto pb-4 px-1 -mx-4 md:mx-0 md:px-0 hide-scrollbar scroll-smooth">
            {recommendedProducts.map((prod) => (
              <div 
                key={prod.id} 
                className="flex-shrink-0 w-[150px] sm:w-[180px] md:w-[220px] bg-white/70 backdrop-blur-md rounded-2xl border border-zinc-950/8 p-3 flex flex-col justify-between hover:border-zinc-950/15 hover:shadow-lg transition-all duration-300"
              >
                {/* Product Image */}
                <div className="w-full aspect-square rounded-xl bg-zinc-50 overflow-hidden mb-3">
                  <img 
                    src={prod.image} 
                    alt={prod.name} 
                    loading="lazy"
                    className="w-full h-full object-cover"
                  />
                </div>
                {/* Product Text */}
                <div className="flex flex-col flex-1 px-1">
                  <h3 className="text-xs font-mono font-bold tracking-wider text-zinc-950 truncate">
                    {prod.name}
                  </h3>
                  <div className="flex justify-between items-center mt-3 pt-2 border-t border-zinc-100">
                    <span className="text-[12px] font-bold text-zinc-900 font-mono">
                      {prod.price}
                    </span>
                    <span className="text-[10px] font-bold text-zinc-500 flex items-center gap-0.5 font-mono">
                      ★ {prod.rating}
                    </span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </section>

        {/* 📚 新着のおすすめ (Main Article List) */}
        <section className="w-full pt-4">
          <div className="flex items-center justify-between mb-6 border-b border-zinc-300/50 pb-2">
            <h2 className="text-base md:text-lg font-bold text-zinc-800 tracking-wider font-sans">
              新着のおすすめ
            </h2>
            <p className="text-zinc-500 font-bold text-[11px] font-mono">NEW RELEASES</p>
          </div>

          {recentArticles.length > 0 ? (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-x-6 gap-y-10">
              {recentArticles.map((article, idx) => (
                <React.Fragment key={article.id}>
                  <Link 
                    href={`/articles/${article.slug}`} 
                    className="group flex flex-col bg-white/70 backdrop-blur-md rounded-2xl p-3 border border-zinc-950/8 hover:border-zinc-950/15 hover:shadow-lg transition-all duration-300"
                  >
                    <div className="aspect-[16/9] w-full rounded-xl bg-zinc-50 relative overflow-hidden mb-3 flex items-center justify-center">
                      {article.coverImage ? (
                        <img 
                          src={article.coverImage} 
                          alt={article.title} 
                          loading="lazy"
                          className="object-cover w-full h-full transform transition-transform duration-750 group-hover:scale-101" 
                        />
                      ) : (
                        <div className="w-full h-full flex items-center justify-center bg-zinc-100 text-zinc-300 text-sm font-mono tracking-widest font-bold">
                          NO IMAGE
                        </div>
                      )}
                      {/* Clean Badge */}
                      <div className="absolute top-3 left-3 bg-zinc-950 px-2 py-0.5 rounded text-[9px] font-mono font-bold text-white tracking-widest uppercase">
                        NEW
                      </div>
                    </div>
                    
                    <div className="flex flex-col flex-1 px-1">
                      <p className="text-[10px] font-bold text-zinc-400 font-mono mb-1.5">
                        {(() => {
                          const d = new Date(article.publishedAt || "");
                          return isNaN(d.getTime()) ? '' : d.toLocaleDateString('ja-JP');
                        })()}
                      </p>
                      <h3 className="article-title text-sm font-bold text-zinc-900 leading-snug group-hover:text-zinc-500 transition-colors line-clamp-2">
                        {article.title}
                      </h3>
                    </div>
                  </Link>
                  {/* First card ad injection */}
                  {idx === 0 && (
                    <div className="col-span-1 sm:col-span-2 lg:col-span-3 flex justify-center w-full">
                      <AdBanner type="large" />
                    </div>
                  )}
                </React.Fragment>
              ))}
            </div>
          ) : (
             <div className="text-center py-20 bg-white rounded-2xl border border-zinc-200/50">
              <span className="text-3xl mb-4 block font-mono">Ø</span>
              <p className="text-sm text-zinc-800 font-bold mb-1 font-mono">NO ARTICLES FOUND</p>
              <p className="text-zinc-500 text-xs font-bold">Discordで記事を生成してください。</p>
            </div>
          )}
          
          <div className="mt-12 text-center">
            <Link 
              href="/articles" 
              className="inline-flex items-center justify-center px-10 py-3 rounded-full border border-zinc-800 text-zinc-900 font-bold text-xs hover:bg-zinc-900 hover:text-white transition-colors tracking-widest font-mono"
            >
              VIEW ALL ARTICLES
            </Link>
          </div>
        </section>

      </div>
    </div>
  );
}
