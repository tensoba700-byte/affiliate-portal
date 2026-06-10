import Link from 'next/link';

export const columnsData = [
  {
    slug: 'night-pore-reset',
    title: '仕事帰りの10分でできる！夕方の毛穴に絶望しないための夜のリセット習慣',
    excerpt: '日中は忙しすぎてメイク直しをする暇なんて1秒もない！そんな大忙しな大人のために、お風呂前にサッとできる、その日の汚れを完全に溜め込まない極上スキンケアメソッド。',
    date: '2026.06.09',
    category: 'ESSAY & TIPS',
    coverImage: 'https://images.unsplash.com/photo-1556228720-195a672e8a03?w=600&q=80'
  },
  {
    slug: 'honest-makeup-base',
    title: 'コスメオタク美容ライターの本音。本当に「夕方ににじまない」メイク下地の選び方',
    excerpt: '「キープ力抜群！」と謳う下地はたくさんあるけれど、本当に夕方までテカらず、ヨレない本命下地を見分けるための成分とテクスチャーのチェックリスト。',
    date: '2026.06.08',
    category: 'BEAUTY CHECKLIST',
    coverImage: 'https://images.unsplash.com/photo-1608248597279-f99d160bfcbc?w=600&q=80'
  },
  {
    slug: 'morning-three-minute-glow',
    title: '忙しい朝の3分間で透明感を引き出す、プチプラを賢く使った時短保湿術',
    excerpt: '1分1秒が惜しい朝のバタバタタイムに、プチプラシートマスクと乳液の組み合わせだけで、夕方まで乾燥知らずのもちもち肌を作るオタクの裏ワザを大公開！',
    date: '2026.06.05',
    category: 'MORNING ROUTINE',
    coverImage: 'https://images.unsplash.com/photo-1598440947619-2c35fc9aa908?w=600&q=80'
  }
];

export default function SampleColumnList() {
  return (
    <div className="s-col-page">

      {/* Hero */}
      <div className="s-col-hero">
        <nav className="s-breadcrumb" style={{ justifyContent: 'center', marginBottom: 24 }}>
          <Link href="/sample">HOME</Link>
          <span className="s-breadcrumb-sep">/</span>
          <span>BEAUTY JOURNAL</span>
        </nav>
        <p className="s-col-hero-kicker">Beauty Journal</p>
        <h1 className="s-col-hero-title">Stories</h1>
        <p className="s-col-hero-sub">ESSAYS, TIPS &amp; EXPERIENCES BY BEAUTY GEEKS</p>
        <div className="s-col-hero-rule" />
      </div>

      {/* Featured */}
      {columnsData.length > 0 && (
        <section className="s-col-featured">
          <Link
            href={`/sample/column/${columnsData[0].slug}`}
            className="s-col-featured-card"
          >
            <div
              className="s-col-featured-img"
              style={{ backgroundImage: `url(${columnsData[0].coverImage})` }}
            />
            <div className="s-col-featured-body">
              <div>
                <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 12 }}>
                  <span className="s-column-cat">{columnsData[0].category}</span>
                  <span style={{ fontFamily: 'var(--s-font-mono)', fontSize: 9, fontWeight: 700, letterSpacing: '0.1em', color: 'var(--s-muted-2)' }}>{columnsData[0].date}</span>
                </div>
                <h2 className="s-col-featured-title">{columnsData[0].title}</h2>
                <p className="s-col-featured-excerpt">{columnsData[0].excerpt}</p>
              </div>
              <div className="s-article-read-more">
                READ THE ESSAY <span>→</span>
              </div>
            </div>
          </Link>
        </section>
      )}

      {/* Grid */}
      <section className="s-col-grid">
        {columnsData.slice(1).map((col) => (
          <Link
            href={`/sample/column/${col.slug}`}
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
                <p className="s-col-grid-excerpt">{col.excerpt}</p>
              </div>
              <div className="s-col-foot">
                <span style={{ fontFamily: 'var(--s-font-mono)', fontSize: 9, fontWeight: 700, letterSpacing: '0.12em', color: 'var(--s-muted-2)' }}>{col.date}</span>
                <div className="s-article-read-more" style={{ paddingTop: 0, borderTop: 'none', marginTop: 0 }}>
                  READ <span>→</span>
                </div>
              </div>
            </div>
          </Link>
        ))}
      </section>

    </div>
  );
}
