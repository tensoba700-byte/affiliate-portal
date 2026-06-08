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
      // Remove forced <br /> tags inside paragraphs to restore natural flow on mobile
      article.content = article.content.replace(/<p>([\s\S]*?)<\/p>/g, (match, pContent) => {
        return `<p>${pContent.replace(/<br\s*\/?>/gi, '')}</p>`;
      });
    }
  } catch (error) {
    article = null;
  }

  if (!article) {
    notFound();
  }

  // Determine the next article recommendation
  const otherSlug = slug === '20260609-cleansing-balm' ? '20260608-toner' : '20260609-cleansing-balm';
  const otherTitle = slug === '20260609-cleansing-balm'
    ? '砂漠肌をもちもちに！夕方まで乾燥知らずのプチプラ実力派化粧水6選'
    : '夕方の毛穴に絶望したくない！大忙し美容オタクが本音で選ぶ最強クレンジングバーム7選';
  const otherImage = slug === '20260609-cleansing-balm'
    ? 'https://images.unsplash.com/photo-1598440947619-2c35fc9aa908?w=600&q=80'
    : 'https://images.unsplash.com/photo-1556228720-195a672e8a03?w=600&q=80';

  return (
    <div className="w-full pb-32 bg-background text-foreground min-h-screen relative overflow-x-hidden">
      {/* Force clean-science theme dynamically */}
      <script dangerouslySetInnerHTML={{
        __html: `
          document.documentElement.setAttribute('data-theme', 'clean-science');
          document.documentElement.setAttribute('data-font', 'sans');
        `
      }} />

      {/* Subtle top background decorative glow */}
      <div className="absolute top-0 left-1/2 -translate-x-1/2 w-full max-w-7xl h-[500px] bg-gradient-to-b from-zinc-200/40 via-zinc-100/10 to-transparent pointer-events-none blur-3xl z-0" />

      <div className="container mx-auto max-w-3xl px-4 pt-10 relative z-10">

        {/* Navigation Breadcrumbs */}
        <nav className="text-[10px] font-bold mb-8 flex items-center justify-start gap-2 text-muted tracking-widest uppercase" aria-label="パンくずリスト">
          <Link href="/sample" className="hover:text-primary transition-colors">HOME</Link>
          <span className="text-zinc-400" aria-hidden="true">/</span>
          <span className="text-muted">VERIFICATION REPORT</span>
          <span className="text-zinc-400" aria-hidden="true">/</span>
          <span className="text-foreground truncate max-w-[180px] md:max-w-none" aria-current="page">
            {article.title}
          </span>
        </nav>

        {/* Eyecatch Image Area */}
        <div className="rounded-2xl overflow-hidden border border-card-border shadow-sm mb-8 bg-white transition-transform duration-500 hover:scale-[1.005]">
          <EyecatchImage slug={slug} alt={article.title} />
        </div>
        
        {/* Clean Science Hero Card */}
        <header className="bg-white rounded-2xl p-6 md:p-12 border border-card-border shadow-sm mb-8 relative overflow-hidden">
          {/* Subtle geometric line for styling */}
          <div className="absolute top-0 right-0 w-32 h-32 bg-gradient-to-bl from-zinc-100 to-transparent pointer-events-none" />
          
          <div className="flex items-center gap-2 mb-6">
            <span className="bg-zinc-950 text-white px-3 py-1 rounded text-[9px] font-black tracking-widest uppercase">
              本音検証
            </span>
            <span className="text-[9px] font-bold text-muted tracking-widest uppercase font-mono">
              LAB REPORT
            </span>
          </div>
          
          <h1 className="article-title text-xl md:text-3xl font-black text-foreground leading-snug mb-8 tracking-tight">
            {article.title}
          </h1>
          
          {/* Metadata Block */}
          <div className="flex flex-wrap items-center justify-between gap-4 pt-6 border-t border-zinc-100 text-[11px] text-muted font-bold">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-full bg-zinc-950 text-white flex items-center justify-center text-xs font-black font-mono shadow-sm">
                M
              </div>
              <div>
                <p className="text-foreground">みっけ！編集部・検証チーム</p>
                <p className="text-[9px] text-muted uppercase font-mono tracking-wider">beauty experts</p>
              </div>
            </div>
            <div className="flex items-center gap-4">
              <span>🗓 {article.publishedAt ? new Date(article.publishedAt).toLocaleDateString('ja-JP') : '2026.06.09'}</span>
              <span>⏱ 読了目安: 5分</span>
            </div>
          </div>
          
          {/* Excerpt verdict card */}
          {article.excerpt && (
            <div className="mt-8 bg-zinc-50 border border-zinc-100 rounded-xl p-5 md:p-6 text-xs md:text-sm font-bold text-zinc-700 leading-relaxed relative">
              <span className="absolute -top-3 left-4 bg-zinc-900 text-white text-[8px] font-mono px-2.5 py-0.5 rounded tracking-widest uppercase">
                EXECUTIVE SUMMARY
              </span>
              <p className="flex gap-2">
                <span className="text-base leading-none">💡</span>
                <span>{article.excerpt}</span>
              </p>
            </div>
          )}
        </header>

        {/* Main Content Area */}
        <div className="bg-white rounded-2xl p-6 md:p-12 border border-card-border shadow-sm mb-8">
          
          {/* Ranking Table wrapped in style overrides */}
          {article.rankings.length > 0 && (
            <div className="w-full mb-12">
              {/* Mobile Swipe Hint */}
              <div className="flex justify-between items-center mb-3 text-[10px] font-bold text-muted px-1">
                <span className="flex items-center gap-1">📊 本音検証スコア比較表</span>
                <span className="md:hidden text-zinc-400">◀ 横スクロールで全項目表示 ▶</span>
              </div>
              <div className="clean-science-table-wrapper">
                <RankingTable
                  products={article.rankings}
                  title="検証エントリー製品ランキング"
                />
              </div>
            </div>
          )}

          {/* Rendered HTML content */}
          {article.content && (
            <div className="rich-text-container cute-html-content mt-8" dangerouslySetInnerHTML={{ __html: article.content }} />
          )}

          {/* Social Share buttons */}
          <div className="mt-16 pt-8 border-t border-zinc-100 flex flex-col items-center gap-4">
            <span className="text-[9px] font-black tracking-widest text-muted uppercase">SHARE THIS REPORT</span>
            <ShareButtons
              url={`https://www.mikke-style.com/articles/${article.slug}`}
              title={article.title}
            />
          </div>
        </div>

        {/* Beauty Writer Profile Card (Persona Match) */}
        <div className="bg-white rounded-2xl p-6 md:p-8 border border-card-border shadow-sm mb-8 flex flex-col sm:flex-row gap-5 items-center sm:items-start">
          <div className="w-16 h-16 rounded-full bg-zinc-100 border border-zinc-200 flex-shrink-0 flex items-center justify-center text-3xl shadow-inner">
            👩🏻‍💻
          </div>
          <div className="text-center sm:text-left space-y-2">
            <div className="flex flex-col sm:flex-row sm:items-center gap-1.5 justify-center sm:justify-start">
              <span className="text-sm font-black text-foreground">ツキ（みっけ！専属美容ライター）</span>
              <span className="bg-zinc-100 text-zinc-800 text-[8px] font-black px-2 py-0.5 rounded-full w-fit mx-auto sm:mx-0">
                本音レビュアー
              </span>
            </div>
            <p className="text-xs text-muted leading-relaxed font-bold">
              仕事も趣味も毎日バタバタ大忙しで、日中に化粧直しをする暇なんて全くないけれど、コスメへの愛だけは誰にも負けない20代後半の等身大オタク。実生活で使い倒した「時短」「夕方に崩れない」リアルな検証をお届けします！
            </p>
          </div>
        </div>

        {/* Recommended Next Report Card */}
        <div className="bg-zinc-950 text-white rounded-2xl p-6 md:p-8 border border-zinc-900 shadow-md mb-8 flex flex-col md:flex-row items-center justify-between gap-6 transition-all duration-300 hover:bg-zinc-900">
          <div className="flex-1 space-y-3">
            <span className="inline-block bg-white/10 text-white px-2 py-0.5 rounded text-[8px] font-bold tracking-widest uppercase">
              RECOMMENDED NEXT REPORT
            </span>
            <h3 className="text-sm md:text-base font-black leading-snug tracking-tight">
              {otherTitle}
            </h3>
            <p className="text-[10px] text-zinc-400">
              あわせて読みたい！お肌のポテンシャルを引き出す本音検証レポート。
            </p>
            <Link 
              href={`/sample/articles/${otherSlug}`}
              className="inline-flex items-center gap-1 text-xs font-black pt-2 text-white border-b border-white/30 hover:border-white transition-all"
            >
              レポートを読む →
            </Link>
          </div>
          <div 
            className="w-full md:w-28 aspect-video md:aspect-square bg-cover bg-center rounded-xl flex-shrink-0 border border-white/10"
            style={{ backgroundImage: `url(${otherImage})` }}
          />
        </div>

        {/* Back Link */}
        <div className="text-center pt-8">
          <Link 
            href="/sample" 
            className="inline-flex items-center gap-2 bg-white hover:bg-zinc-50 border border-card-border rounded-full px-8 py-3 text-xs font-black transition-all shadow-sm"
          >
            ← ホームに戻る
          </Link>
        </div>

      </div>
    </div>
  );
}
