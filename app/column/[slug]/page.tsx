import Link from 'next/link';
import { notFound } from 'next/navigation';
import { getColumnBySlug, getAllColumns } from '@/src/lib/columns';
import { getArticleBySlug } from '@/src/lib/api';
import type { Metadata } from 'next';

export const dynamic = 'force-dynamic';

export async function generateStaticParams() {
  const columns = await getAllColumns();
  return columns.map((c) => ({ slug: c.slug }));
}

interface PageProps {
  params: Promise<{ slug: string }>;
}

export async function generateMetadata({ params }: PageProps): Promise<Metadata> {
  const { slug } = await params;
  const column = await getColumnBySlug(slug);
  if (!column) return {};

  const cleanTitle = column.title.replace(/<br\s*\/?>/gi, '');
  const imageUrl = column.coverImage.startsWith('/') 
    ? `https://www.mikke-style.com${column.coverImage}` 
    : column.coverImage;

  return {
    title: cleanTitle,
    description: column.description,
    alternates: {
      canonical: `/column/${column.slug}`,
    },
    openGraph: {
      title: cleanTitle,
      description: column.description,
      url: `https://www.mikke-style.com/column/${column.slug}`,
      images: [
        {
          url: imageUrl,
          width: 1200,
          height: 630,
          alt: cleanTitle,
        },
      ],
      type: 'article',
    },
    twitter: {
      card: 'summary_large_image',
      title: cleanTitle,
      description: column.description,
      images: [imageUrl],
    },
  };
}

export default async function ColumnDetailPage({ params }: PageProps) {
  const { slug } = await params;
  const column = await getColumnBySlug(slug);

  if (!column) {
    notFound();
  }

  const allColumns = await getAllColumns();
  const currentIndex = allColumns.findIndex(c => c.slug === slug);
  let nextColumn = null;
  if (allColumns.length > 1 && currentIndex !== -1) {
    nextColumn = allColumns[(currentIndex + 1) % allColumns.length];
  }

  // 関連記事 (related_articles) のデータを取得
  const relatedArticlesData = await Promise.all(
    column.related_articles.map(async (rSlug) => {
      return await getArticleBySlug(rSlug);
    })
  );
  const validRelatedArticles = relatedArticlesData.filter((art): art is NonNullable<typeof art> => art !== null);

  // 日付の整形 (2026.06.12)
  let formattedDate = '2026.06.12';
  if (column.publishDate) {
    const cleanDate = column.publishDate.split(' ')[0];
    formattedDate = cleanDate.replace(/-/g, '.');
  }

  const cleanColumnTitle = column.title.replace(/<br\s*\/?>/gi, '');

  // JSON-LD 構造化データ
  const jsonLd = {
    '@context': 'https://schema.org',
    '@type': 'Article',
    'headline': cleanColumnTitle,
    'description': column.description,
    'image': [column.coverImage.startsWith('/') ? `https://www.mikke-style.com${column.coverImage}` : column.coverImage],
    'datePublished': column.publishDate ? new Date(column.publishDate.replace(' ', 'T') + '+09:00').toISOString() : new Date().toISOString(),
    'author': {
      '@type': 'Person',
      'name': 'ツキ',
      'url': 'https://www.mikke-style.com',
    },
    'publisher': {
      '@type': 'Organization',
      'name': 'みっけ！',
      'logo': {
        '@type': 'ImageObject',
        'url': 'https://www.mikke-style.com/favicon.svg',
      },
    },
  };

  return (
    <div className="s-col-detail s-article-page">
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }}
      />

      {/* Breadcrumb */}
      <nav className="s-breadcrumb">
        <Link href="/">HOME</Link>
        <span className="s-breadcrumb-sep">/</span>
        <Link href="/column">JOURNAL</Link>
        <span className="s-breadcrumb-sep">/</span>
        <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', maxWidth: 150 }} aria-current="page">
          {column.category}
        </span>
      </nav>

      {/* Column Header */}
      <header className="s-article-header-card" style={{ textAlign: 'center' }}>
        <div className="s-article-eyebrow" style={{ justifyContent: 'center' }}>
          <span className="s-badge-primary">{column.category}</span>
          <span style={{ fontFamily: 'var(--s-font-mono)', fontSize: 9, fontWeight: 700, letterSpacing: '0.14em', textTransform: 'uppercase', color: 'var(--s-muted)' }}>BEAUTY JOURNAL ESSAY</span>
        </div>
        <h1 className="s-article-h1" style={{ textAlign: 'center', fontFamily: 'var(--font-noto-serif), serif', textWrap: 'balance' }}>{cleanColumnTitle}</h1>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 20, fontSize: 11, fontWeight: 600, color: 'var(--s-muted)', paddingTop: 16, borderTop: '1px solid var(--s-border-soft)' }}>
          <span>✍️ WRITTEN BY: ツキ</span>
          <span>🗓 {formattedDate}</span>
        </div>
      </header>

      {/* Cover Image */}
      <div
        style={{
          width: '100%',
          aspectRatio: '21/9',
          borderRadius: 'var(--s-radius-card)',
          overflow: 'hidden',
          backgroundImage: `url(${column.coverImage})`,
          backgroundSize: 'cover',
          backgroundPosition: 'center',
          border: '1px solid var(--s-border)',
          marginBottom: 24,
        }}
      />

      {/* Index (Table of Contents) */}
      {column.headings.length > 0 && (
        <div className="s-toc-card" style={{ padding: '20px', background: 'var(--s-surface-2)', borderRadius: 'var(--s-radius-card)', border: '1px solid var(--s-border)', marginBottom: '32px' }}>
          <h2 style={{ fontFamily: 'var(--s-font-serif)', fontSize: '18px', fontWeight: 'bold', marginBottom: '12px', borderBottom: '1.5px solid var(--s-accent)', paddingBottom: '4px', display: 'inline-block', color: 'var(--s-ink)' }}>INDEX</h2>
          <ul style={{ listStyleType: 'none', paddingLeft: 0, margin: 0, display: 'flex', flexDirection: 'column', gap: '8px' }}>
            {column.headings.map((h) => (
              <li key={h.id} style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                <span style={{ color: 'var(--s-accent)', fontSize: '10px' }}>✦</span>
                <a href={`#${h.id}`} style={{ fontSize: '13px', color: 'var(--s-ink-2)', textDecoration: 'none', fontWeight: '600' }} className="hover:underline">
                  {h.text}
                </a>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Content */}
      <div className="s-content-card">
        <article
          className="s-rich-text cute-html-content"
          dangerouslySetInnerHTML={{ __html: column.contentHtml }}
        />
      </div>

      {/* Writer Profile */}
      <div className="s-profile-card">
        <div className="s-profile-avatar">👩🏻‍💻</div>
        <div>
          <div className="s-profile-name">
            ツキ（みっけ！専属美容ライター）
            <span className="s-profile-badge">ライター</span>
          </div>
          <p className="s-profile-desc">
            仕事も趣味も毎日バタバタ大忙しで、日中に化粧直しをする暇なんて全くないけれど、コスメへの愛だけは誰にも負けない20代後半の等身大オタク。コスメ好きライターが調べ尽くした情報をお届けします。
          </p>
        </div>
      </div>

      {/* Related Verification Reports */}
      {validRelatedArticles.length > 0 && (
        <div style={{ marginTop: '48px', marginBottom: '24px' }}>
          <h3 style={{ fontFamily: 'var(--s-font-serif)', fontSize: '20px', fontWeight: 'bold', marginBottom: '20px', borderBottom: '2px solid var(--s-border-soft)', paddingBottom: '10px', color: 'var(--s-ink)' }}>
            🔗 関連記事（このコスメのガチ検証）
          </h3>
          <div className="s-article-grid">
            {validRelatedArticles.map((article) => {
              let dateStr = '2026.06.12';
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
                    <img
                      src={article.coverImage || '/eyecatch/20260609-cleansing-balm-sample.png'}
                      alt={cleanTitle}
                      className="s-article-img"
                      loading="lazy"
                    />
                    <span className="s-article-thumb-badge">RECOMMENDED</span>
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
        </div>
      )}

      {/* Next Column */}
      {nextColumn && (
        <div className="s-next-card">
          <div style={{ flex: 1 }}>
            <div className="s-next-eyebrow">NEXT JOURNAL</div>
            <h3 className="s-next-title">{nextColumn.title.replace(/<br\s*\/?>/gi, '')}</h3>
            <Link href={`/column/${nextColumn.slug}`} className="s-next-link">
              コラムを読む →
            </Link>
          </div>
          <div
            className="s-next-thumb"
            style={{ backgroundImage: `url(${nextColumn.coverImage})` }}
          />
        </div>
      )}

      {/* Back */}
      <div style={{ textAlign: 'center', paddingTop: 8 }}>
        <Link href="/column" className="s-back-btn">
          ← コラム一覧に戻る
        </Link>
      </div>
    </div>
  );
}
