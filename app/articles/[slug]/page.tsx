import { getArticleBySlug, getAllArticles, getRelatedArticles } from '@/src/lib/api';
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
  
  const ogImage = article.coverImage || '/og-image.png';

  return {
    title: article.title,
    description: article.excerpt || `徹底比較！ ${article.title} のおすすめ情報`,
    openGraph: {
      title: article.title,
      description: article.excerpt,
      url: `https://mikke-style.com/articles/${slug}`,
      type: 'article',
      images: [{ url: ogImage }],
    },
    twitter: {
      card: 'summary_large_image',
      title: article.title,
      description: article.excerpt,
      images: [ogImage],
    },
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

  const relatedArticles = await getRelatedArticles(slug, article.category || "");

  // Structured Data (JSON-LD)
  const jsonLd = {
    '@context': 'https://schema.org',
    '@type': 'Article',
    headline: article.title,
    description: article.excerpt,
    image: article.coverImage,
    datePublished: article.publishedAt,
    author: {
      '@type': 'Organization',
      name: 'みっけ！',
    },
  };

  return (
    <>
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }}
      />
      <article className="w-full pb-24 animate-fade-in-up bg-background">
        
        <div className="container mx-auto max-w-3xl px-4 pt-8">
          
          {/* Navigation (Breadcrumbs) */}
          <nav className="text-[10px] md:text-xs font-bold mb-6 flex items-center justify-center gap-2 text-muted" aria-label="パンくずリスト">
            <Link href="/" className="hover:text-primary transition-colors">ホーム</Link>
            <span className="text-primary/30" aria-hidden="true">&gt;</span>
            <Link href="/articles" className="hover:text-primary transition-colors">記事一覧</Link>
            {article.category && (
              <>
                <span className="text-primary/30" aria-hidden="true">&gt;</span>
                <Link href={`/search?category=${encodeURIComponent(article.category)}`} className="hover:text-primary transition-colors">{article.category}</Link>
              </>
            )}
            <span className="text-primary/30" aria-hidden="true">&gt;</span>
            <span className="text-foreground truncate max-w-[150px]" aria-current="page">{article.title}</span>
          </nav>
          
          {/* 🌸 Cute Article Hero */}
          <header className="bg-white rounded-[2rem] p-6 md:p-10 cute-shadow border border-card-border mb-8 text-center relative overflow-hidden">
            <div className="absolute top-0 right-0 w-32 h-32 bg-primary/5 rounded-bl-[100px] pointer-events-none"></div>
            
            <div className="inline-block bg-primary/10 text-primary px-4 py-1.5 rounded-full text-xs font-black mb-6">
              Review
            </div>
            
            <h1 className="text-2xl md:text-3xl lg:text-4xl font-black leading-snug mb-6 text-foreground">
              {article.title}
            </h1>
            
            <time dateTime={article.publishedAt} className="text-xs font-bold text-muted block mb-6">
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
                <img src={article.coverImage} alt={article.title} loading="lazy" className="w-full h-full object-cover" />
              </div>
            </div>
          )}

          {/* 📝 Article Content Area */}
          <div className="bg-white rounded-[2rem] p-6 md:p-10 cute-shadow border border-card-border mb-12">

            {/* 🏆 Ranking Table */}
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
              url={`https://mikke-style.com/articles/${article.slug}`}
              title={article.title}
              isGadget={article.title.includes('ガジェット') || article.slug.includes('ガジェット')}
            />
          </div>

          {/* 🎀 Related Articles Section */}
          {relatedArticles.length > 0 && (
            <section className="mt-16">
              <h2 className="text-xl md:text-2xl font-black text-foreground mb-8 text-center flex items-center justify-center gap-2">
                <span className="text-primary">🌈</span> あわせて見たい記事
              </h2>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                {relatedArticles.map((rel) => (
                  <Link 
                    key={rel.slug} 
                    href={`/articles/${rel.slug}`}
                    className="group bg-white rounded-3xl p-3 cute-shadow border border-card-border hover:-translate-y-1 transition-all duration-300"
                  >
                    <div className="aspect-[4/3] rounded-2xl overflow-hidden mb-3 bg-primary/5">
                      {rel.coverImage ? (
                        <img src={rel.coverImage} alt={rel.title} loading="lazy" className="w-full h-full object-cover group-hover:scale-110 transition-transform duration-500" />
                      ) : (
                        <div className="w-full h-full flex items-center justify-center text-2xl">🎀</div>
                      )}
                    </div>
                    <h3 className="text-sm font-black text-foreground group-hover:text-primary transition-colors line-clamp-2 leading-snug">
                      {rel.title}
                    </h3>
                  </Link>
                ))}
              </div>
            </section>
          )}

        </div>
      </article>
    </>
  );
}
