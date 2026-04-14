import { getAllArticles, ArticleItem } from '@/src/lib/api';
import { AdBanner } from '@/src/components/AdBanner';

export default async function Home() {
  let recentArticles: ArticleItem[] = [];
  try {
    const articles = await getAllArticles();
    recentArticles = articles.slice(0, 6);
  } catch (error) {
    console.error("Failed to fetch articles:", error);
  }

  // Cute Categories
  const categories = [
    { id: '1', name: 'Beauty & Skincare', jp: '美容・スキンケア', image: '/images/category_beauty_1775564212926.png' },
    { id: '2', name: 'Tech & Gadgets', jp: 'ガジェット', image: '/images/cat_gadget_1775565122276.png' },
    { id: '3', name: 'Interior', jp: 'インテリア', image: '/images/category_lifestyle_1775564225940.png' },
    { id: '4', name: 'Daily Goods', jp: '生活雑貨', image: '/images/cat_daily_1775565137707.png' },
    { id: '5', name: 'Useful Goods', jp: '便利グッズ', image: '/images/cat_useful_1775565153706.png' },
  ];

  return (
    <div className="flex flex-col items-center w-full pb-24 overflow-x-hidden">
      
      {/* 🌸 Cute Hero Section */}
      <section className="w-full relative px-6 pt-20 pb-28 flex flex-col items-center justify-center min-h-[50vh] animate-fade-in-up">
        {/* Soft background blobs */}
        <div className="absolute top-10 left-[10%] w-[50vw] h-[50vw] bg-primary/10 rounded-full blur-[80px] -z-10 mix-blend-multiply pointer-events-none"></div>
        <div className="absolute bottom-10 right-[10%] w-[40vw] h-[40vw] bg-yellow-300/10 rounded-full blur-[60px] -z-10 mix-blend-multiply pointer-events-none"></div>

        <div className="container mx-auto text-center max-w-3xl z-10">
          <div className="inline-flex items-center gap-2 px-6 py-2 rounded-full bg-white cute-shadow text-sm font-bold text-primary mb-8 animate-float">
            <span className="text-lg">✨</span>
            あなたにぴったりのアイテムがここに
          </div>
          
          <h1 className="text-4xl md:text-5xl lg:text-7xl font-black mb-6 text-foreground leading-[1.2] tracking-normal">
            お気に入りを、<br className="md:hidden" />
            <span className="text-primary relative inline-block">
              みっけ！
              <svg className="absolute -bottom-2 md:-bottom-4 left-0 w-full" viewBox="0 0 200 20" preserveAspectRatio="none">
                <path d="M0,10 Q100,20 200,5" fill="none" stroke="currentColor" strokeWidth="8" strokeLinecap="round" className="text-primary/30" />
              </svg>
            </span>
          </h1>
          <p className="text-base md:text-xl text-muted font-bold max-w-2xl mx-auto mb-10 leading-relaxed">
            暮らしをちょっと可愛く、もっと楽しく。<br className="hidden md:block" />
            話題のアイテムから隠れた名品まで徹底レビュー♡
          </p>
        </div>
      </section>

      {/* 🌟 Cute Category Cards */}
      <section className="w-full px-4 -mt-10 relative z-20">
        <div className="container mx-auto max-w-6xl">
          {/* Responsive grid for all viewports */}
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-3 md:gap-5 px-2">
            {categories.map((cat, i) => (
              <Link 
                key={cat.id} 
                href={`/search?category=${encodeURIComponent(cat.jp)}`} 
                className="group relative h-40 md:h-64 lg:h-72 rounded-[1.5rem] md:rounded-[2rem] overflow-hidden cute-shadow block transform transition-all duration-300 hover:-translate-y-2 hover:shadow-xl animate-fade-in-up"
                style={{ animationDelay: `${i * 80}ms` }}
              >
                <div className="absolute inset-0 bg-gradient-to-t from-black/60 via-black/20 to-transparent z-10 duration-500"></div>
                {/* Image */}
                <img 
                  src={cat.image} 
                  alt={cat.jp} 
                  loading="lazy"
                  className="absolute inset-0 w-full h-full object-cover transition-transform duration-700 group-hover:scale-110"
                />
                {/* Text Content */}
                <div className="absolute inset-x-0 bottom-0 p-3 md:p-6 z-20 text-center">
                  <h3 className="text-sm md:text-lg lg:text-xl font-black text-white leading-tight drop-shadow-md">
                    {cat.jp}
                  </h3>
                </div>
              </Link>
            ))}
          </div>
        </div>
      </section>

      {/* 📚 Main Article List */}
      <section className="w-full pt-20 md:pt-32 px-6">
        <div className="container mx-auto max-w-5xl">
          <div className="flex flex-col items-center justify-center mb-12 text-center">
            <h2 className="text-2xl md:text-3xl font-black text-foreground mb-3 flex items-center gap-2">
              <span className="text-primary">💌</span> 新着のおすすめ
            </h2>
            <p className="text-muted font-bold text-sm">毎日のお買い物がもっと楽しくなる情報をピックアップ！</p>
          </div>

          {recentArticles.length > 0 ? (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-x-6 gap-y-10">
              {recentArticles.map((article, idx) => (
                <React.Fragment key={article.id}>
                  <Link 
                    href={`/articles/${article.slug}`} 
                    className="group flex flex-col bg-white rounded-[2rem] p-3 cute-shadow hover:shadow-xl transition-all duration-500 hover:-translate-y-2 border border-card-border"
                  >
                    <div className="aspect-[16/9] w-full rounded-3xl bg-gray-50 relative overflow-hidden mb-4">
                      {article.coverImage ? (
                        // @ts-ignore
                        <img src={article.coverImage} alt={article.title} className="absolute inset-0 object-cover object-center w-full h-full transform transition-transform duration-700 group-hover:scale-110" />
                      ) : (
                        <div className="w-full h-full flex items-center justify-center bg-primary/5 text-primary/30">
                          <span className="text-3xl">🎀</span>
                        </div>
                      )}
                      {/* Cute Badge */}
                      <div className="absolute top-3 left-3 bg-white px-3 py-1 rounded-full text-[10px] font-black text-primary shadow-sm border border-primary/10">
                        NEW
                      </div>
                    </div>
                    
                    <div className="flex flex-col flex-1 px-3 pb-2 text-center">
                      <p className="text-[10px] font-bold text-primary mb-2">
                        {new Date(article.publishedAt || "").toLocaleDateString('ja-JP')}
                      </p>
                      <h3 className="text-base font-black text-foreground mb-2 leading-snug group-hover:text-primary transition-colors line-clamp-2">
                        {article.title}
                      </h3>
                    </div>
                  </Link>
                  {/* 先頭カードの下に広告⑤〜⑦をランダム表示 */}
                  {idx === 0 && (
                    <div className="col-span-1 sm:col-span-2 lg:col-span-3 flex justify-center w-full">
                      <AdBanner type="large" />
                    </div>
                  )}
                </React.Fragment>
              ))}
            </div>
          ) : (
             <div className="text-center py-20 bg-white rounded-3xl border border-card-border cute-shadow">
              <span className="text-5xl mb-4 block">🥺</span>
              <p className="text-lg text-foreground font-black mb-2">まだ記事がありません</p>
              <p className="text-muted font-bold text-sm">Discordでかわいい記事を生成してね！</p>
            </div>
          )}
          
          <div className="mt-16 text-center">
            <Link href="/articles" className="inline-flex items-center justify-center px-12 py-4 rounded-full bg-primary text-white font-black text-sm hover:bg-primary/90 transition-all duration-300 shadow-lg hover:shadow-primary/30 hover:-translate-y-1">
              もっと見る 👀
            </Link>
          </div>
        </div>
      </section>
    </div>
  );
}
