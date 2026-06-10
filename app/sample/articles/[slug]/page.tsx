import { getArticleBySlug } from '@/src/lib/api';
import { notFound } from 'next/navigation';
import Link from 'next/link';
import RankingTable from '@/src/components/RankingTable';
import { EyecatchImage } from '@/src/components/EyecatchImage';
import ShareButtons from '@/src/components/ShareButtons';

export async function generateStaticParams() {
  return [
    { slug: '20260609-cleansing-balm' },
    { slug: '20260608-toner' }
  ];
}

interface PageProps {
  params: Promise<{ slug: string }>;
}

export default async function SampleArticleDetail({ params }: PageProps) {
  const { slug } = await params;

  if (slug !== '20260609-cleansing-balm' && slug !== '20260608-toner') {
    notFound();
  }

  let article;
  try {
    article = await getArticleBySlug(slug);
    if (article && article.content) {
      article.content = article.content.replace(/<p>([\s\S]*?)<\/p>/g, (match: string, pContent: string) => {
        return `<p>${pContent.replace(/<br\s*\/?>/gi, '')}</p>`;
      });
    }
  } catch (error) {
    article = null;
  }

  if (!article) {
    notFound();
  }

  const otherSlug = slug === '20260609-cleansing-balm' ? '20260608-toner' : '20260609-cleansing-balm';
  const otherTitle = slug === '20260609-cleansing-balm'
    ? '砂漠肌をもちもちに！夕方まで乾燥知らずのプチプラ実力派化粧水6選'
    : '夕方の毛穴に絶望したくない！大忙し美容オタクが本音で選ぶ最強クレンジングバーム7選';
  const otherImage = slug === '20260609-cleansing-balm'
    ? 'https://images.unsplash.com/photo-1598440947619-2c35fc9aa908?w=600&q=80'
    : 'https://images.unsplash.com/photo-1556228720-195a672e8a03?w=600&q=80';

  return (
    <div className="s-article-detail s-article-page">

      {/* Breadcrumb */}
      <nav className="s-breadcrumb" aria-label="パンくずリスト">
        <Link href="/sample">HOME</Link>
        <span className="s-breadcrumb-sep">/</span>
        <span>VERIFICATION REPORT</span>
        <span className="s-breadcrumb-sep">/</span>
        <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', maxWidth: 180 }} aria-current="page">
          {article.title}
        </span>
      </nav>

      {/* Eyecatch */}
      <div className="s-eyecatch-wrap">
        <EyecatchImage slug={slug} alt={article.title} />
      </div>

      {/* Article Header Card */}
      <header className="s-article-header-card">
        <div className="s-article-eyebrow">
          <span className="s-badge-primary">本音検証</span>
          <span style={{ fontFamily: 'var(--s-font-mono)', fontSize: 9, fontWeight: 700, letterSpacing: '0.14em', textTransform: 'uppercase', color: 'var(--s-muted)' }}>LAB REPORT</span>
        </div>

        <h1 className="s-article-h1">{article.title}</h1>

        <div className="s-article-meta">
          <div className="s-author-chip">
            <div className="s-author-avatar">m</div>
            <div>
              <div className="s-author-name">みっけ！編集部・検証チーム</div>
              <div className="s-author-role">beauty experts</div>
            </div>
          </div>
          <div className="s-article-meta-right">
            <span>🗓 {article.publishedAt ? new Date(article.publishedAt).toLocaleDateString('ja-JP') : '2026.06.09'}</span>
            <span>⏱ 読了目安: 5分</span>
          </div>
        </div>

        {article.excerpt && (
          <div className="s-executive-summary">
            <span className="s-executive-summary-label">EXECUTIVE SUMMARY</span>
            <p>💡 {article.excerpt}</p>
          </div>
        )}
      </header>

      {/* Content Card */}
      <div className="s-content-card">
        {article.rankings.length > 0 && (
          <div style={{ marginBottom: 48 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
              <span style={{ fontFamily: 'var(--s-font-mono)', fontSize: 9, fontWeight: 700, letterSpacing: '0.14em', textTransform: 'uppercase', color: 'var(--s-muted)' }}>
                📊 本音検証スコア比較表
              </span>
              <span style={{ fontSize: 10, color: 'var(--s-muted-2)', fontWeight: 600 }} className="hidden-md">◀ 横スクロールで全項目表示 ▶</span>
            </div>
            <div className="s-table-wrap">
              <RankingTable
                products={article.rankings}
                title="検証エントリー製品ランキング"
              />
            </div>
          </div>
        )}

        {article.content && (
          <div
            className="s-rich-text"
            dangerouslySetInnerHTML={{ __html: article.content }}
          />
        )}

        <div style={{ marginTop: 48, paddingTop: 24, borderTop: '1px solid var(--s-border)', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 16 }}>
          <span style={{ fontFamily: 'var(--s-font-mono)', fontSize: 9, fontWeight: 700, letterSpacing: '0.14em', textTransform: 'uppercase', color: 'var(--s-muted)' }}>
            SHARE THIS REPORT
          </span>
          <ShareButtons
            url={`https://www.mikke-style.com/articles/${article.slug}`}
            title={article.title}
          />
        </div>
      </div>

      {/* Writer Profile */}
      <div className="s-profile-card">
        <div className="s-profile-avatar">👩🏻‍💻</div>
        <div>
          <div className="s-profile-name">
            ツキ（みっけ！専属美容ライター）
            <span className="s-profile-badge">本音レビュアー</span>
          </div>
          <p className="s-profile-desc">
            仕事も趣味も毎日バタバタ大忙しで、日中に化粧直しをする暇なんて全くないけれど、コスメへの愛だけは誰にも負けない20代後半の等身大オタク。実生活で使い倒した「時短」「夕方に崩れない」リアルな検証をお届けします！
          </p>
        </div>
      </div>

      {/* Next Report */}
      <div className="s-next-card">
        <div style={{ flex: 1 }}>
          <div className="s-next-eyebrow">RECOMMENDED NEXT REPORT</div>
          <h3 className="s-next-title">{otherTitle}</h3>
          <p className="s-next-sub">あわせて読みたい！お肌のポテンシャルを引き出す本音検証レポート。</p>
          <Link href={`/sample/articles/${otherSlug}`} className="s-next-link">
            レポートを読む →
          </Link>
        </div>
        <div
          className="s-next-thumb"
          style={{ backgroundImage: `url(${otherImage})` }}
        />
      </div>

      {/* Back */}
      <div style={{ textAlign: 'center', paddingTop: 16 }}>
        <Link href="/sample" className="s-back-btn">
          ← ホームに戻る
        </Link>
      </div>

    </div>
  );
}
