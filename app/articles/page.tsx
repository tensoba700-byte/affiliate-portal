import Link from 'next/link';
import { getAllArticles, ArticleItem } from '@/src/lib/api';

export const metadata = {
  title: 'すべての記事 | みっけ！',
  description: '最新の商品比較・おすすめ記事の一覧です。',
  alternates: {
    canonical: '/articles',
  },
};

export default async function ArticlesPage() {
  let articles: ArticleItem[] = [];
  try {
    articles = await getAllArticles();
  } catch (error) {
    console.error("Failed to fetch articles:", error);
  }

  return (
    <div className="flex flex-col items-center w-full pb-32 pt-10 px-4 overflow-hidden">
      <div className="container mx-auto max-w-5xl animate-fade-in-up">
        
        {/* Header Breadcrumbs & Title */}
        <div className="mb-12 text-center">
          <nav className="text-[10px] sm:text-xs text-muted font-bold mb-4 flex items-center justify-center gap-2">
            <Link href="/" className="hover:text-primary transition-colors">ホーム</Link>
            <span className="text-primary/30">&gt;</span>
            <span className="text-foreground">すべての記事</span>
          </nav>
          <h1 className="text-3xl md:text-4xl font-black text-foreground mb-4 flex items-center justify-center gap-2">
            <span className="text-primary">💐</span> 記事一覧
          </h1>
          <p className="text-sm text-muted font-bold">
            気になるアイテムの記事をみつけてね！
          </p>
        </div>

        {articles.length > 0 ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-x-6 gap-y-10">
            {articles.map((article, i) => (
              <Link 
                href={`/articles/${article.slug}`} 
                key={article.id}
                className="group flex flex-col bg-white rounded-[2rem] p-3 cute-shadow hover:shadow-xl transition-all duration-500 hover:-translate-y-2 border border-card-border animate-fade-in-up"
                style={{ animationDelay: `${(i % 3) * 100}ms` }}
              >
                <div className="aspect-video w-full rounded-3xl bg-gray-50 relative overflow-hidden mb-4 flex items-center justify-center">
                  {article.coverImage ? (
                    // @ts-ignore
                    <img src={article.coverImage} alt={article.title} className="object-contain max-w-full max-h-full w-full h-full transform transition-transform duration-700 group-hover:scale-102" />
                  ) : (
                    <div className="w-full h-full flex items-center justify-center bg-primary/5 text-primary/30 cursor-pointer">
                       <span className="text-3xl">🎀</span>
                    </div>
                  )}
                </div>
                <div className="flex flex-col flex-1 px-3 pb-2 text-center">
                  <p className="text-[10px] font-bold text-primary mb-2">
                    {(() => {
                      const d = new Date(article.publishedAt || "");
                      return isNaN(d.getTime()) ? '' : d.toLocaleDateString('ja-JP');
                    })()}
                  </p>
                  <h2 className="article-title text-base font-black text-foreground mb-2 leading-snug group-hover:text-primary transition-colors line-clamp-2">
                    {article.title}
                  </h2>
                  <p className="text-muted text-xs line-clamp-2 mt-auto leading-relaxed font-bold">
                    {article.excerpt || "くわしく見る！"}
                  </p>
                </div>
              </Link>
            ))}
          </div>
        ) : (
          <div className="text-center py-20 bg-white rounded-3xl border border-card-border cute-shadow">
            <span className="text-5xl mb-4 block">🥺</span>
            <p className="text-lg text-foreground font-black mb-2">まだ記事がありません</p>
            <p className="text-muted font-bold text-sm">Discordでかわいい記事を生成してね！</p>
          </div>
        )}
      </div>
    </div>
  );
}
