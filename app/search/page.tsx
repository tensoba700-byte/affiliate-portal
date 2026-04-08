import Link from 'next/link';
import { getAllArticles } from '@/src/lib/api';

export const metadata = {
  title: '検索結果 | みっけ！',
  description: '検索結果一覧です。',
};

export default async function SearchPage({
  searchParams,
}: {
  searchParams: Promise<{ q?: string }>;
}) {
  const resolvedParams = await searchParams;
  const rawQuery = resolvedParams.q || "";
  const query = rawQuery.trim().toLowerCase();

  let allArticles = [];
  try {
    allArticles = await getAllArticles();
  } catch (error) {
    console.error("Failed to fetch articles for search:", error);
  }

  // Filter articles based on query
  const results = query
    ? allArticles.filter((article) => {
        const titleMatch = article.title?.toLowerCase().includes(query);
        const excerptMatch = article.excerpt?.toLowerCase().includes(query);
        return titleMatch || excerptMatch;
      })
    : [];

  return (
    <div className="flex flex-col items-center w-full pb-32 pt-10 px-4 overflow-hidden min-h-[70vh]">
      <div className="container mx-auto max-w-5xl animate-fade-in-up">
        
        {/* Header Breadcrumbs & Search Info */}
        <div className="mb-12 text-center">
          <nav className="text-[10px] sm:text-xs text-muted font-bold mb-6 flex items-center justify-center gap-2">
            <Link href="/" className="hover:text-primary transition-colors">ホーム</Link>
            <span className="text-primary/30">&gt;</span>
            <span className="text-foreground">検索結果</span>
          </nav>

          <h1 className="text-2xl md:text-3xl font-black text-foreground mb-4">
            「<span className="text-primary px-1">{rawQuery || "キーワード未入力"}</span>」のさがしもの
          </h1>
          <p className="text-sm text-muted font-bold">
            {results.length} 件の記事がみつかりました！
          </p>
        </div>

        {/* Search Results */}
        {results.length > 0 ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-x-6 gap-y-10">
            {results.map((article, i) => (
              <Link 
                href={`/articles/${article.slug}`} 
                key={article.id}
                className="group flex flex-col bg-white rounded-[2rem] p-3 cute-shadow hover:shadow-xl transition-all duration-500 hover:-translate-y-2 border border-card-border animate-fade-in-up"
                style={{ animationDelay: `${(i % 3) * 100}ms` }}
              >
                <div className="aspect-square sm:aspect-[4/3] w-full rounded-3xl bg-gray-50 relative overflow-hidden mb-4">
                  {article.coverImage ? (
                    // @ts-ignore
                    <img src={article.coverImage} alt={article.title} className="object-cover w-full h-full transform transition-transform duration-700 group-hover:scale-105" />
                  ) : (
                    <div className="w-full h-full flex items-center justify-center bg-primary/5 text-primary/30 cursor-pointer">
                       <span className="text-3xl">🎀</span>
                    </div>
                  )}
                </div>
                <div className="flex flex-col flex-1 px-3 pb-2 text-center">
                  <p className="text-[10px] font-bold text-primary mb-2">
                    {new Date(article.publishDate || "").toLocaleDateString('ja-JP')}
                  </p>
                  <h2 className="text-base font-black text-foreground mb-2 leading-snug group-hover:text-primary transition-colors line-clamp-2">
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
          <div className="text-center py-20 bg-white rounded-3xl border border-card-border cute-shadow max-w-xl mx-auto">
            <span className="text-5xl mb-4 block">💦</span>
            <p className="text-xl text-foreground font-black mb-3">ごめんなさい！みつかりませんでした</p>
            <p className="text-muted font-bold text-sm leading-relaxed">
              「{rawQuery}」に一致する記事はありませんでした。<br />
              別のキーワードでさがしてみてね！
            </p>
            <div className="mt-8">
              <Link href="/articles" className="inline-block px-10 py-3 rounded-full bg-primary/10 text-primary font-black text-sm hover:bg-primary hover:text-white transition-all duration-300">
                すべての記事一覧にもどる
              </Link>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
