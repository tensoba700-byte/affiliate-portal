import { getAllArticles, ArticleItem } from '@/src/lib/api';
import Link from 'next/link';
import Image from 'next/image';

export const dynamic = 'force-dynamic';

export const metadata = {
  title: 'すべての記事 | みっけ！',
  description: '最新の商品比較・おすすめ記事の一覧です。',
  alternates: {
    canonical: '/articles',
  },
};

interface PageProps {
  searchParams: Promise<{ page?: string }>;
}

export default async function ArticlesPage({ searchParams }: PageProps) {
  const resolvedParams = await searchParams;
  const currentPage = parseInt(resolvedParams.page || '1', 10);
  const limit = 12; // 1ページあたり12件

  let articles: ArticleItem[] = [];
  try {
    articles = await getAllArticles();
  } catch (error) {
    console.error("Failed to fetch articles:", error);
  }

  const totalArticles = articles.length;
  const totalPages = Math.ceil(totalArticles / limit);
  const page = Math.max(1, Math.min(currentPage, totalPages || 1));
  const pagedArticles = articles.slice((page - 1) * limit, page * limit);

  return (
    <div className="s-prod-page">
      {/* Breadcrumbs */}
      <nav className="s-breadcrumb" style={{ marginBottom: 24, justifyContent: 'center' }}>
        <Link href="/">HOME</Link>
        <span className="s-breadcrumb-sep">/</span>
        <span aria-current="page">VERIFIED REPORTS</span>
      </nav>

      {/* Header */}
      <header className="s-prod-header">
        <h1 className="s-prod-title">Verified Reports</h1>
        <p className="s-prod-subtitle">ガチ検証レポート記事一覧</p>
      </header>

      {/* Articles Grid */}
      {pagedArticles.length > 0 ? (
        <>
          <div className="s-article-grid">
            {pagedArticles.map((article) => {
              let dateStr = '2026.06.09';
              if (article.publishedAt) {
                const d = new Date(article.publishedAt);
                if (!isNaN(d.getTime())) {
                  dateStr = d.toLocaleDateString('ja-JP').replace(/\//g, '.');
                }
              }

              const cleanTitle = article.title.replace(/<br\s*\/?>/gi, '');
              return (
                <Link
                  key={article.slug}
                  href={`/articles/${article.slug}`}
                  className="s-article-card"
                >
                  <div className="s-article-thumb">
                    <Image 
                      src={article.coverImage || '/eyecatch/20260609-cleansing-balm-sample.png'} 
                      alt={cleanTitle} 
                      className="s-article-img"
                      width={380}
                      height={240}
                    />
                    <span className="s-article-thumb-badge">NEW REPORT</span>
                  </div>
                  <div className="s-article-body">
                    <span className="s-article-date">{dateStr}</span>
                    <h3 className="s-article-title">{cleanTitle}</h3>
                    <p className="s-article-excerpt">{article.excerpt || '大人気コスメを本音でガチ検証レビュー！メイク落ちや使用感を徹底的に解説するよ。'}</p>
                    <div className="s-article-read-more">
                      READ REPORT <span>→</span>
                    </div>
                  </div>
                </Link>
              );
            })}
          </div>

          {/* Pagination Controls */}
          {totalPages > 1 && (
            <div className="s-pagination">
              {page > 1 && (
                <Link href={`/articles?page=${page - 1}`} className="s-pagination-btn">
                  &larr; 前へ
                </Link>
              )}
              {Array.from({ length: totalPages }).map((_, idx) => {
                const pageNum = idx + 1;
                return (
                  <Link
                    key={pageNum}
                    href={`/articles?page=${pageNum}`}
                    className={`s-pagination-num ${page === pageNum ? 's-pagination-num-active' : ''}`}
                  >
                    {pageNum}
                  </Link>
                );
              })}
              {page < totalPages && (
                <Link href={`/articles?page=${page + 1}`} className="s-pagination-btn">
                  次へ &rarr;
                </Link>
              )}
            </div>
          )}
        </>
      ) : (
        <div style={{ textAlign: 'center', padding: '48px 0', color: 'var(--s-muted-2)', fontWeight: 'bold' }}>
          まだ記事がありません。
        </div>
      )}
    </div>
  );
}

