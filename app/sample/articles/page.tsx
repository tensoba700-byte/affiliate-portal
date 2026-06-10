import { getArticleBySlug } from '@/src/lib/api';
import Link from 'next/link';

export default async function SampleArticlesPage() {
  const balmArticle = await getArticleBySlug('20260609-cleansing-balm');
  const tonerArticle = await getArticleBySlug('20260608-toner');

  // サンプルのアイキャッチ画像を流用するために、coverImage を sample/prod 用に書き換え
  const articles = [
    ...(balmArticle ? [{ 
        ...balmArticle, 
        coverImage: '/eyecatch/20260609-cleansing-balm-sample.png' 
      }] : []),
    ...(tonerArticle ? [{ 
        ...tonerArticle, 
        coverImage: '/eyecatch/20260608-toner.png' 
      }] : [])
  ];

  return (
    <div className="s-prod-page">
      {/* Breadcrumbs */}
      <nav className="s-breadcrumb" style={{ marginBottom: 24, justifyContent: 'center' }}>
        <Link href="/sample">HOME</Link>
        <span className="s-breadcrumb-sep">/</span>
        <span aria-current="page">VERIFIED REPORTS</span>
      </nav>

      {/* Header */}
      <header className="s-prod-header">
        <h1 className="s-prod-title">Verified Reports</h1>
        <p className="s-prod-subtitle">ガチ検証レポート記事一覧</p>
      </header>

      {/* Articles Grid */}
      <div className="s-article-grid">
        {articles.map((article) => (
          <Link
            key={article.slug}
            href={`/sample/articles/${article.slug}`}
            className="s-article-card"
          >
            <div className="s-article-thumb">
              <img 
                src={article.coverImage || ''} 
                alt={article.title} 
                className="s-article-img"
                loading="lazy"
              />
              <span className="s-article-thumb-badge">NEW REPORT</span>
            </div>
            <div className="s-article-body">
              <span className="s-article-date">
                {(() => {
                  const d = new Date(article.publishedAt || "");
                  return isNaN(d.getTime()) ? '2026.06.09' : d.toLocaleDateString('ja-JP').replace(/\//g, '.');
                })()}
              </span>
              <h3 className="s-article-title">{article.title}</h3>
              <p className="s-article-excerpt">{article.excerpt}</p>
              <div className="s-article-read-more">
                READ REPORT <span>→</span>
              </div>
            </div>
          </Link>
        ))}
      </div>
    </div>
  );
}
