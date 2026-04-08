import { getArticleBySlug, getAllArticles } from '@/src/lib/api';
import { notFound } from 'next/navigation';
import Link from 'next/link';
import { documentToReactComponents } from '@contentful/rich-text-react-renderer';
import RankingTable from '@/src/components/RankingTable';
import ShareButtons from '@/src/components/ShareButtons';

export async function generateStaticParams() {
  try {
    const articles = await getAllArticles();
    return articles.map((article) => ({
      slug: article.slug,
    }));
  } catch (e) {
    return [];
  }
}

export async function generateMetadata({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;
  const article = await getArticleBySlug(slug);
  if (!article) return { title: 'Not Found' };
  
  return {
    title: `${article.title} | みっけ！`,
    description: article.excerpt || `徹底比較！ ${article.title} のおすすめ情報`,
  };
}

export default async function ArticleDetail({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;
  
  let article;
  try {
    article = await getArticleBySlug(slug);
  } catch (error) {
    article = null;
  }

  if (!article) {
    notFound();
  }

  return (
    <article className="w-full pb-24 animate-fade-in-up bg-background">
      
      <div className="container mx-auto max-w-3xl px-4 pt-8">
        
        {/* Navigation */}
        <nav className="text-[10px] md:text-xs font-bold mb-6 flex items-center justify-center gap-2 text-muted">
          <Link href="/" className="hover:text-primary transition-colors">ホーム</Link>
          <span className="text-primary/30">&gt;</span>
          <Link href="/articles" className="hover:text-primary transition-colors">記事一覧</Link>
          <span className="text-primary/30">&gt;</span>
          <span className="text-foreground truncate max-w-[150px]">{article.title}</span>
        </nav>
        
        {/* 🌸 Cute Article Hero */}
        <header className="bg-white rounded-[2rem] p-6 md:p-10 cute-shadow border border-card-border mb-8 text-center relative overflow-hidden">
          {/* Decorative Corner blobs */}
          <div className="absolute top-0 right-0 w-32 h-32 bg-primary/5 rounded-bl-[100px] pointer-events-none"></div>
          
          <div className="inline-block bg-primary/10 text-primary px-4 py-1.5 rounded-full text-xs font-black mb-6">
            Review
          </div>
          
          <h1 className="text-2xl md:text-3xl lg:text-4xl font-black leading-snug mb-6 text-foreground">
            {article.title}
          </h1>
          
          <time className="text-xs font-bold text-muted block mb-6">
            🗓 {new Date(article.publishedAt || "").toLocaleDateString('ja-JP')}
          </time>
          
          {article.excerpt && (
            <p className="text-sm md:text-base font-bold text-foreground bg-background rounded-2xl p-4 inline-block text-left">
              💡 {article.excerpt}
            </p>
          )}
        </header>

        {/* Cover Image */}
        {article.coverImage && (
          <div className="w-full aspect-[4/3] md:aspect-[16/9] bg-white rounded-[2rem] p-3 cute-shadow border border-card-border mb-8">
            <div className="w-full h-full rounded-3xl overflow-hidden relative">
              {/* @ts-ignore */}
              <img src={article.coverImage} alt={article.title} className="w-full h-full object-cover" />
            </div>
          </div>
        )}

        {/* 📝 Article Content Area */}
        <div className="bg-white rounded-[2rem] p-6 md:p-10 cute-shadow border border-card-border">

          {/* 🏆 Ranking Table — ランキングが存在する記事のみ表示 */}
          {article.rankings.length > 0 && (
            <RankingTable
              products={article.rankings}
              title={`${article.title} ランキング`}
            />
          )}

          {article.content ? (
            <div className="rich-text-container cute-html-content" dangerouslySetInnerHTML={{ __html: article.content ?? '' }} />
          ) : article.body ? (
            <div className="rich-text-container cute-html-content">
              {documentToReactComponents(article.body)}
            </div>
          ) : null}
          
          {/* Share Section */}
          <ShareButtons
            url={`https://example.com/articles/${article.slug}`}
            title={article.title}
            isGadget={article.title.includes('ガジェット') || article.slug.includes('ガジェット')}
          />
        </div>

      </div>
    </article>
  );
}
