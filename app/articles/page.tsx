import { getAllArticles, ArticleItem } from '@/src/lib/api';
import Link from 'next/link';

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
      {articles.length > 0 ? (
        <div className="s-article-grid">
          {articles.map((article) => {
            let dateStr = '2026.06.09';
            if (article.publishedAt) {
              const d = new Date(article.publishedAt);
              if (!isNaN(d.getTime())) {
                dateStr = d.toLocaleDateString('ja-JP').replace(/\//g, '.');
              }
            }

            return (
              <Link
                key={article.slug}
                href={`/articles/${article.slug}`}
                className="s-article-card"
              >
                <div className="s-article-thumb">
                  <img 
                    src={article.coverImage || '/eyecatch/20260609-cleansing-balm-sample.png'} 
                    alt={article.title} 
                    className="s-article-img"
                    loading="lazy"
                  />
                  <span className="s-article-thumb-badge">NEW REPORT</span>
                </div>
                <div className="s-article-body">
                  <span className="s-article-date">{dateStr}</span>
                  <h3 className="s-article-title">{article.title}</h3>
                  <p className="s-article-excerpt">{article.excerpt || '大人気コスメを本音でガチ検証レビュー！メイク落ちや使用感を徹底的に解説するよ。'}</p>
                  <div className="s-article-read-more">
                    READ REPORT <span>→</span>
                  </div>
                </div>
              </Link>
            );
          })}
        </div>
      ) : (
        <div style={{ textAlign: 'center', padding: '48px 0', color: 'var(--s-muted-2)', fontWeight: 'bold' }}>
          まだ記事がありません。
        </div>
      )}
    </div>
  );
}

