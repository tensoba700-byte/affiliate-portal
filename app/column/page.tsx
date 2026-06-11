import Link from 'next/link';
import { getAllColumns, ColumnItem } from '@/src/lib/columns';

export const revalidate = 3600; // Revalidate cache hourly (ISR)

export const metadata = {
  title: '美容コラム | みっけ！',
  description: '美容オタクの専属ライターが綴る、夕方ににじまない・時短でお肌をいたわる美容エッセイ・スキンケア知識コラム一覧。',
  alternates: {
    canonical: '/column',
  },
};

export default async function ColumnListPage() {
  let columns: ColumnItem[] = [];
  try {
    const allCols = await getAllColumns();
    columns = Array.isArray(allCols) ? allCols : [];
  } catch (e) {
    console.error("Failed to load columns:", e);
  }

  return (
    <div className="s-col-page">
      {/* Hero */}
      <div className="s-col-hero">
        <nav className="s-breadcrumb" style={{ justifyContent: 'center', marginBottom: 24 }}>
          <Link href="/">HOME</Link>
          <span className="s-breadcrumb-sep">/</span>
          <span>BEAUTY JOURNAL</span>
        </nav>
        <p className="s-col-hero-kicker">Beauty Journal</p>
        <h1 className="s-col-hero-title">Stories</h1>
        <p className="s-col-hero-sub">ESSAYS, TIPS &amp; EXPERIENCES BY BEAUTY GEEKS</p>
        <div className="s-col-hero-rule" />
      </div>

      {/* Featured Column (First item) */}
      {columns.length > 0 ? (
        <section className="s-col-featured">
          {(() => {
            const featured = columns[0];
            let dateStr = '2026.06.12';
            if (featured.publishDate) {
              dateStr = featured.publishDate.split(' ')[0].replace(/-/g, '.');
            }
            return (
              <Link
                href={`/column/${featured.slug}`}
                className="s-col-featured-card"
              >
                <div
                  className="s-col-featured-img"
                  style={{ backgroundImage: `url(${featured.coverImage})` }}
                />
                <div className="s-col-featured-body">
                  <div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 12 }}>
                      <span className="s-column-cat">{featured.category}</span>
                      <span style={{ fontFamily: 'var(--s-font-mono)', fontSize: 9, fontWeight: 700, letterSpacing: '0.1em', color: 'var(--s-muted-2)' }}>{dateStr}</span>
                    </div>
                    <h2 className="s-col-featured-title">{featured.title}</h2>
                    <p className="s-col-featured-excerpt">{featured.description}</p>
                  </div>
                  <div className="s-article-read-more">
                    READ THE ESSAY <span>→</span>
                  </div>
                </div>
              </Link>
            );
          })()}
        </section>
      ) : (
        <div style={{ textAlign: 'center', padding: '48px 0', color: 'var(--s-muted-2)', fontWeight: 'bold' }}>
          現在コラムはありません
        </div>
      )}

      {/* Column Grid (Items after the first) */}
      {columns.length > 1 && (
        <section className="s-col-grid">
          {columns.slice(1).map((col) => {
            let dateStr = '2026.06.12';
            if (col.publishDate) {
              dateStr = col.publishDate.split(' ')[0].replace(/-/g, '.');
            }
            return (
              <Link
                href={`/column/${col.slug}`}
                key={col.slug}
                className="s-col-grid-card"
              >
                <div
                  className="s-col-grid-img"
                  style={{ backgroundImage: `url(${col.coverImage})` }}
                />
                <div className="s-col-grid-body">
                  <div>
                    <span className="s-column-cat">{col.category}</span>
                    <h3 className="s-col-grid-title" style={{ marginTop: 8 }}>{col.title}</h3>
                    <p className="s-col-grid-excerpt">{col.description}</p>
                  </div>
                  <div className="s-col-foot">
                    <span style={{ fontFamily: 'var(--s-font-mono)', fontSize: 9, fontWeight: 700, letterSpacing: '0.12em', color: 'var(--s-muted-2)' }}>{dateStr}</span>
                    <div className="s-article-read-more" style={{ paddingTop: 0, borderTop: 'none', marginTop: 0 }}>
                      READ <span>→</span>
                    </div>
                  </div>
                </div>
              </Link>
            );
          })}
        </section>
      )}
    </div>
  );
}
