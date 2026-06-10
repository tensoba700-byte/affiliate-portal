import React from 'react';
import Link from 'next/link';

export default function SampleHome() {
  const latestArticles = [
    {
      slug: '20260609-cleansing-balm',
      title: '夕方の毛穴に絶望したくない！大忙し美容オタクが本音で選ぶ最強クレンジングバーム7選',
      excerpt: '仕事に趣味に大忙しで日中の化粧直しはゼロ！メイクも毛穴汚れも一気にリセットできる最強のクレンジングバームを本音レビュー！',
      date: '2026.06.09',
      category: '毛穴・くすみリセット',
      image: 'https://images.unsplash.com/photo-1556228720-195a672e8a03?w=600&q=80'
    },
    {
      slug: '20260608-toner',
      title: '砂漠肌をもちもちに！夕方まで乾燥知らずのプチプラ実力派化粧水6選',
      excerpt: '冷房や乾燥でカサカサになりがちなお肌に、たっぷり惜しみなく使えるプチプラなのにデパコス級のしっとり感を得られる本命化粧水。',
      date: '2026.06.08',
      category: 'プチプラ実力派',
      image: 'https://images.unsplash.com/photo-1598440947619-2c35fc9aa908?w=600&q=80'
    }
  ];

  const latestColumns = [
    {
      slug: 'night-pore-reset',
      title: '仕事帰りの10分でできる！夕方の毛穴に絶望しないための夜のリセット習慣',
      date: '2026.06.09',
      category: 'ESSAY'
    },
    {
      slug: 'honest-makeup-base',
      title: 'コスメオタク美容ライターの本音。本当に「夕方ににじまない」メイク下地の選び方',
      date: '2026.06.08',
      category: 'BEAUTY TIPS'
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
      articleLabel: '最強クレンジングバーム7選'
    },
    { 
      id: '2', 
      name: '無印良品 敏感肌用化粧水', 
      price: '¥1,290', 
      rating: '4.7', 
      type: 'TONER',
      articleSlug: '20260608-toner',
      articleLabel: 'プチプラ実力派化粧水6選'
    }
  ];

  return (
    <div className="flex flex-col items-center w-full pb-32 bg-background text-foreground min-h-screen relative overflow-x-hidden">
      {/* Force clean-science theme dynamically */}
      <script dangerouslySetInnerHTML={{
        __html: `
          document.documentElement.setAttribute('data-theme', 'clean-science');
          document.documentElement.setAttribute('data-font', 'sans');
        `
      }} />

      {/* Top ambient decorative glow */}
      <div className="absolute top-0 left-1/2 -translate-x-1/2 w-full max-w-7xl h-[450px] bg-gradient-to-b from-zinc-200/40 via-zinc-100/10 to-transparent pointer-events-none blur-3xl z-0" />

      {/* 📰 Feature Hero Banner (Pattern B) */}
      <section className="w-full max-w-4xl px-4 mt-8 relative z-10">
        <div 
          className="w-full h-[340px] md:h-[400px] rounded-2xl relative overflow-hidden border border-card-border shadow-sm bg-cover bg-center transition-all duration-700 hover:shadow-md"
          style={{ 
            backgroundImage: 'url("https://images.unsplash.com/photo-1556228720-195a672e8a03?w=1200&q=80")',
            filter: 'brightness(0.95)'
          }}
        >
          <div className="absolute inset-0 bg-black/15"></div>
          
          {/* Overlay glass panel */}
          <div className="absolute bottom-5 left-5 right-5 bg-white/95 backdrop-blur-md border border-card-border rounded-xl p-5 md:p-8 flex flex-col gap-2 shadow-sm">
            <div className="flex items-center gap-2">
              <span className="text-[9px] font-black text-white bg-zinc-950 px-2 py-0.5 rounded tracking-widest uppercase">FEATURE</span>
              <span className="text-[9px] font-bold text-muted tracking-widest uppercase font-mono">EDITORIAL EDITION</span>
            </div>
            <h2 className="text-base md:text-xl font-black text-foreground leading-snug">
              時間がない！でも妥協したくない！忙しい女子のための「ガチ本音」コスメ検証メディア
            </h2>
            <p className="text-muted text-xs font-bold leading-relaxed max-w-2xl">
              仕事に趣味に毎日バタバタで、メイク直しをする暇なんて一切ないけれど、コスメへの愛だけは誰にも負けないツキが運営する「みっけ！(mikke!)」。リアルに使い倒して「本当に崩れない」「タイパ最強」と確信したアイテムだけを忖度なしで徹底比較するよ！あなたにぴったりの本命コスメをここで見つけてね！
            </p>
          </div>
        </div>
      </section>

      {/* 🧭 Horizontal Category Navigation Bar */}
      <div className="w-full max-w-4xl px-4 mt-6 relative z-10">
        <div className="w-full bg-white border border-card-border rounded-xl px-5 py-3.5 flex justify-between items-center text-[11px] font-bold text-foreground overflow-x-auto hide-scrollbar whitespace-nowrap gap-6">
          <div className="flex gap-3">
            <Link href="/sample" className="bg-zinc-950 text-white px-3.5 py-1.5 rounded transition-colors">ホーム</Link>
            <Link href="/sample/column" className="text-muted hover:text-primary px-3.5 py-1.5 rounded transition-colors border border-transparent hover:border-zinc-200">美容コラム</Link>
          </div>
          <div className="flex items-center gap-4 text-zinc-300">
            <span>|</span>
            <span className="text-zinc-400 font-bold uppercase tracking-wider text-[10px]">VERIFICATIONS:</span>
            <span className="text-zinc-400 cursor-not-allowed border border-dashed border-zinc-200 px-3 py-1 rounded bg-zinc-50/50">アイテム別</span>
            <span className="text-zinc-400 cursor-not-allowed border border-dashed border-zinc-200 px-3 py-1 rounded bg-zinc-50/50">お悩み別</span>
            <span className="text-zinc-400 cursor-not-allowed border border-dashed border-zinc-200 px-3 py-1 rounded bg-zinc-50/50">プチプラ実力派</span>
          </div>
        </div>
      </div>

      {/* 🛡️ Content Wrapper */}
      <div className="container mx-auto max-w-4xl px-4 mt-10 w-full space-y-16 relative z-10">

        {/* 🛍️ Recommended Items (Horizontal Scroll) */}
        <section className="w-full">
          <div className="flex justify-between items-end mb-5 border-b border-card-border pb-3">
            <div className="space-y-1">
              <h2 className="text-xs font-black text-foreground tracking-widest uppercase flex items-center gap-1.5">
                <span>✦</span> RECOMMENDED ITEMS
              </h2>
              <p className="text-[9px] text-muted font-bold tracking-wider">注目のガチ検証高スコア品</p>
            </div>
            <span className="text-[10px] font-bold text-muted uppercase font-mono">LAB PICK</span>
          </div>
          
          <div className="flex gap-4 overflow-x-auto pb-2 hide-scrollbar">
            {recommendedItems.map((prod) => (
              <div 
                key={prod.id} 
                className="flex-shrink-0 w-[190px] bg-white shadow-sm hover:shadow-md rounded-xl border border-card-border p-4 flex flex-col justify-between hover:-translate-y-0.5 transition-all duration-300"
              >
                <div className="w-full aspect-square rounded-lg bg-zinc-50 border border-card-border overflow-hidden mb-3.5 flex items-center justify-center relative select-none">
                  {/* Styled minimal bottle graphic representation */}
                  <div className="w-10 h-18 border border-zinc-300 rounded bg-white/60 relative flex items-center justify-center">
                    <div className="w-5 h-3 border border-zinc-300 absolute top-[-4px] bg-zinc-900 rounded-sm"></div>
                    <div className="text-[7px] font-mono font-black tracking-widest text-zinc-400 rotate-90 scale-90">{prod.type}</div>
                  </div>
                </div>
                <div>
                  <h3 className="text-xs font-black text-zinc-900 truncate">{prod.name}</h3>
                  <div className="flex justify-between items-center mt-3 pt-2.5 border-t border-zinc-100 text-[11px] font-bold">
                    <span className="text-foreground">{prod.price}</span>
                    <span className="text-muted flex items-center gap-0.5">⭐ {prod.rating}</span>
                  </div>
                  {prod.articleSlug && (
                    <Link 
                      href={`/sample/articles/${prod.articleSlug}`}
                      className="mt-3.5 block text-[9px] font-black text-center text-primary bg-zinc-50 hover:bg-zinc-100 border border-card-border py-2 rounded-lg transition-all hover:scale-[1.01]"
                    >
                      📄 この記事で紹介！
                    </Link>
                  )}
                </div>
              </div>
            ))}
          </div>
        </section>

        {/* 📰 Latest Articles (Real Content) */}
        <section className="w-full">
          <div className="flex justify-between items-end mb-6 border-b border-card-border pb-3">
            <div className="space-y-1">
              <h2 className="text-xs font-black text-foreground tracking-widest uppercase flex items-center gap-1.5">
                <span>✦</span> LATEST VERIFICATIONS
              </h2>
              <p className="text-[9px] text-muted font-bold tracking-wider">編集部が体を張って検証した本音レポート</p>
            </div>
            <span className="text-[10px] font-bold text-muted uppercase font-mono">NEW REPORTS</span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            {latestArticles.map((article) => (
              <Link 
                key={article.slug}
                href={`/sample/articles/${article.slug}`} 
                className="group flex flex-col bg-white border border-card-border rounded-xl hover:shadow-md shadow-sm transition-all duration-500 overflow-hidden"
              >
                <div 
                  className="aspect-[16/9] w-full bg-cover bg-center relative transition-transform duration-700 group-hover:scale-[1.005]"
                  style={{ backgroundImage: `url(${article.image})` }}
                >
                  <div className="absolute top-3 left-3 bg-zinc-950 px-2 py-0.5 rounded text-[8px] font-mono font-black text-white tracking-widest uppercase">
                    NEW REPORT
                  </div>
                </div>
                
                <div className="p-6 flex flex-col flex-1 gap-2">
                  <span className="text-[10px] font-bold text-muted">{article.date}</span>
                  <h3 className="text-base font-black text-foreground leading-snug group-hover:text-zinc-700 transition-colors line-clamp-2">
                    {article.title}
                  </h3>
                  <p className="text-muted text-xs leading-relaxed font-bold line-clamp-2 mt-2">
                    {article.excerpt}
                  </p>
                  <div className="text-[10px] font-black tracking-widest text-primary flex items-center gap-1 group-hover:translate-x-1 transition-transform pt-4 mt-auto">
                    READ REPORT <span className="text-xs">→</span>
                  </div>
                </div>
              </Link>
            ))}
          </div>
        </section>

        {/* 🖋️ Latest Columns (Beauty Blog / Essay) */}
        <section className="w-full">
          <div className="flex justify-between items-end mb-6 border-b border-card-border pb-3">
            <div className="space-y-1">
              <h2 className="text-xs font-black text-foreground tracking-widest uppercase flex items-center gap-1.5">
                <span>✦</span> BEAUTY COLUMN
              </h2>
              <p className="text-[9px] text-muted font-bold tracking-wider">美容オタクライターが綴るお肌のエッセイ</p>
            </div>
            <Link href="/sample/column" className="text-[10px] font-black text-primary hover:opacity-75 transition-opacity tracking-widest uppercase">
              VIEW JOURNAL →
            </Link>
          </div>

          <div className="flex flex-col gap-4">
            {latestColumns.map((col) => (
              <Link
                key={col.slug}
                href={`/sample/column/${col.slug}`}
                className="group flex flex-col sm:flex-row justify-between items-start sm:items-center bg-white border border-card-border p-5 rounded-xl hover:shadow-sm transition-all duration-300 gap-4"
              >
                <div className="flex flex-col gap-1.5">
                  <span className="text-[9px] font-black text-white bg-zinc-950 px-2 py-0.5 rounded w-fit tracking-wider uppercase font-mono">{col.category}</span>
                  <h3 className="text-sm md:text-base font-black text-foreground group-hover:text-zinc-700 transition-colors leading-snug mt-1">
                    {col.title}
                  </h3>
                </div>
                <div className="text-[11px] font-bold text-muted mt-2 sm:mt-0 flex-shrink-0 flex items-center gap-3">
                  <span>{col.date}</span>
                  <span className="text-xs group-hover:translate-x-1 transition-transform">→</span>
                </div>
              </Link>
            ))}
          </div>
        </section>

        {/* 🧪 Background Composite Demo (Multiply vs Original) */}
        <section className="w-full bg-white border border-card-border p-6 rounded-2xl">
          <div className="flex justify-between items-end mb-6 border-b border-card-border pb-3">
            <div className="space-y-1">
              <h2 className="text-xs font-black text-foreground tracking-widest uppercase flex items-center gap-1.5">
                <span>✦</span> BACKGROUND BLEND DEMO (CSS乗算テスト)
              </h2>
              <p className="text-[9px] text-muted font-bold tracking-wider">ECサイトの白背景画像をグレー背景に溶け込ませるデモ</p>
            </div>
            <span className="text-[10px] font-bold text-muted uppercase font-mono">LAB DEMO</span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mt-4">
            {/* Original White Background Card */}
            <div className="border border-card-border rounded-xl p-4 flex flex-col items-center">
              <span className="text-[9px] font-black bg-zinc-100 text-zinc-800 px-2 py-0.5 rounded mb-3">元の画像 (白背景)</span>
              <div className="w-full h-48 bg-zinc-50 border border-zinc-100 rounded-lg flex items-center justify-center overflow-hidden">
                <img 
                  src="https://images.unsplash.com/photo-1601049541289-9b1b7bbbfe19?w=400&q=80" 
                  alt="Original White Background Product" 
                  className="h-full object-contain"
                />
              </div>
              <p className="text-[10px] text-muted font-bold mt-2 text-center">ECサイトによくある典型的な白背景の商品画像</p>
            </div>

            {/* Blended Background Card */}
            <div className="border border-card-border rounded-xl p-4 flex flex-col items-center">
              <span className="text-[9px] font-black bg-zinc-950 text-white px-2 py-0.5 rounded mb-3">CSS乗算後 (グレー背景に溶け込み)</span>
              {/* Wrapped in a container with concrete-like light-grey background */}
              <div 
                className="w-full h-48 rounded-lg flex items-center justify-center overflow-hidden relative"
                style={{ 
                  backgroundColor: '#f4f4f5',
                  backgroundImage: 'radial-gradient(circle, rgba(24,24,27,0.03) 0%, rgba(24,24,27,0.08) 100%)'
                }}
              >
                <img 
                  src="https://images.unsplash.com/photo-1601049541289-9b1b7bbbfe19?w=400&q=80" 
                  alt="Blended Product" 
                  className="h-full object-contain mix-blend-multiply"
                />
              </div>
              <p className="text-[10px] text-muted font-bold mt-2 text-center">CSS乗算を使うと、白背景が消えてグレー背景に自然に馴染むよ！</p>
            </div>
          </div>
        </section>

      </div>
    </div>
  );
}
