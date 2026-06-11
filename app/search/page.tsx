import Link from 'next/link';
import { getAllArticles } from '@/src/lib/api';

export const metadata = {
  title: 'カテゴリー・検索 | みっけ！',
  description: 'カテゴリー別・キーワード検索の記事一覧です。',
  alternates: {
    canonical: '/search',
  },
};

export default async function SearchPage({
  searchParams,
}: {
  searchParams: Promise<{ q?: string; category?: string }>;
}) {
  const resolvedParams = await searchParams;
  const rawQuery = resolvedParams.q || '';
  const rawCategory = resolvedParams.category || '';
  const query = rawQuery.trim().toLowerCase();
  const category = rawCategory.trim();

  let allArticles: any[] = [];
  try {
    allArticles = await getAllArticles();
  } catch (error) {
    console.error('Failed to fetch articles for search:', error);
  }

  // Category filter (exact match, case-insensitive)
  // Keyword search (title + excerpt)
  const results = allArticles.filter((article) => {
    if (category) {
      // Category filter takes priority
      return (article.category || '').toLowerCase() === category.toLowerCase();
    }
    if (query) {
      const titleMatch = article.title?.toLowerCase().includes(query);
      const excerptMatch = article.excerpt?.toLowerCase().includes(query);
      const categoryMatch = article.category?.toLowerCase().includes(query);
      return titleMatch || excerptMatch || categoryMatch;
    }
    return false;
  });

  const isCategory = !!category;
  const pageTitle = isCategory
    ? `${category}の記事`
    : rawQuery
    ? `「${rawQuery}」のさがしもの`
    : 'さがしもの';

  const CATEGORY_EMOJIS: Record<string, string> = {
    'ガジェット': '⚡',
    '美容・スキンケア': '✨',
    'インテリア': '🏠',
    '生活雑貨': '🛒',
    '便利グッズ': '🎯',
  };
  const emoji = isCategory ? (CATEGORY_EMOJIS[category] || '💐') : '🔍';

  return (
    <div className="flex flex-col items-center w-full pb-32 pt-10 px-4 overflow-hidden min-h-[70vh] s-category-page">
      <div className="container mx-auto max-w-5xl animate-fade-in-up">

        {/* Header */}
        <div className="mb-12 text-center">
          <nav className="text-[10px] sm:text-xs text-muted font-bold mb-6 flex items-center justify-center gap-2">
            <Link href="/" className="hover:text-primary transition-colors">ホーム</Link>
            <span className="text-primary/30">&gt;</span>
            <span className="text-foreground">{isCategory ? 'カテゴリー' : '検索結果'}</span>
            {category && (
              <>
                <span className="text-primary/30">&gt;</span>
                <span className="text-foreground">{category}</span>
              </>
            )}
          </nav>

          <h1 className="text-2xl md:text-3xl font-black text-foreground mb-4 flex items-center justify-center gap-2">
            {pageTitle}
          </h1>
          <p className="text-sm text-muted font-bold">
            {results.length} 件の記事がみつかりました！
          </p>
        </div>

        {/* Category Pills (カテゴリーページ時に表示) */}
        {isCategory && (
          <div className="flex flex-wrap gap-3 justify-center mb-10">
            {['美容・スキンケア', 'ガジェット', 'インテリア', '生活雑貨', '便利グッズ'].map((cat) => (
              <Link
                key={cat}
                href={`/search?category=${encodeURIComponent(cat)}`}
                className={`px-5 py-2 rounded-[4px] text-xs font-black transition-all border ${
                  cat === category
                    ? 'bg-primary text-white border-primary shadow-md'
                    : 'bg-white text-muted border-card-border hover:border-primary hover:text-primary'
                }`}
              >
                {cat}
              </Link>
            ))}
          </div>
        )}

        {/* Results */}
        {results.length > 0 ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-x-6 gap-y-10">
            {results.map((article, i) => (
              <Link
                href={`/articles/${article.slug}`}
                key={article.id}
                className="group flex flex-col bg-white rounded-[8px] p-3 cute-shadow hover:shadow-xl transition-all duration-500 hover:-translate-y-2 border border-card-border animate-fade-in-up"
                style={{ animationDelay: `${(i % 3) * 100}ms` }}
              >
                <div className="aspect-video w-full rounded-[4px] bg-gray-50 relative overflow-hidden mb-4 flex items-center justify-center">
                  {article.coverImage ? (
                    // @ts-ignore
                    <img src={article.coverImage} alt={article.title} className="object-contain max-w-full max-h-full w-full h-full transform transition-transform duration-700 group-hover:scale-102" />
                  ) : (
                    <div className="w-full h-full flex items-center justify-center bg-primary/5 text-primary/30 cursor-pointer">
                      <span className="text-xs font-bold text-muted">NO IMAGE</span>
                    </div>
                  )}
                  {article.category && (
                    <div className="absolute top-3 left-3 bg-white px-3 py-1 rounded-[4px] text-[10px] font-black text-primary shadow-sm border border-primary/10">
                      {article.category}
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
                    {article.excerpt || 'くわしく見る！'}
                  </p>
                </div>
              </Link>
            ))}
          </div>
        ) : (
          <div className="text-center py-20 bg-white rounded-[4px] border border-card-border cute-shadow max-w-xl mx-auto">
            <p className="text-xl text-foreground font-black mb-3">
              {isCategory ? 'この カテゴリーはまだ記事がありません' : 'ごめんなさい！みつかりませんでした'}
            </p>
            <p className="text-muted font-bold text-sm leading-relaxed">
              {isCategory
                ? `「${category}」カテゴリーの記事は準備中です。`
                : `「${rawQuery}」に一致する記事はありませんでした。別のキーワードでお試しください。`}
            </p>
            <div className="mt-8 flex flex-col sm:flex-row gap-3 justify-center">
              <Link href="/articles" className="inline-block px-10 py-3 rounded-[4px] bg-primary/10 text-primary font-black text-sm hover:bg-primary hover:text-white transition-all duration-300">
                すべての記事一覧
              </Link>
              <Link href="/" className="inline-block px-10 py-3 rounded-[4px] bg-white border border-card-border text-muted font-black text-sm hover:border-primary hover:text-primary transition-all duration-300">
                トップページへ
              </Link>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
