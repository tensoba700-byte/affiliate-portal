import { getArticleBySlug, getAllArticles, getRelatedArticles } from '@/src/lib/api';
import { notFound } from 'next/navigation';
import Link from 'next/link';
import { documentToReactComponents } from '@contentful/rich-text-react-renderer';
import RankingTable from '@/src/components/RankingTable';
import ShareButtons from '@/src/components/ShareButtons';
import { EyecatchImage } from '@/src/components/EyecatchImage';
import { AdBanner } from '@/src/components/AdBanner';

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
  
  const cleanTitle = article.title.replace(/<br\s*\/?>/gi, '');
  const ogImage = article.coverImage || '/og-image.png';

  return {
    title: cleanTitle,
    description: article.excerpt || `徹底比較！ ${cleanTitle} のおすすめ情報`,
    alternates: {
      canonical: `/articles/${slug}`,
    },
    openGraph: {
      title: cleanTitle,
      description: article.excerpt,
      url: `https://www.mikke-style.com/articles/${slug}`,
      type: 'article',
      images: [{ url: ogImage }],
    },
    twitter: {
      card: 'summary_large_image',
      title: cleanTitle,
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

  const cleanTitle = article.title.replace(/<br\s*\/?>/gi, '');
  const relatedArticles = await getRelatedArticles(slug, article.category || "");

  // Structured Data (JSON-LD)
  const jsonLdList: any[] = [
    {
      '@context': 'https://schema.org',
      '@type': 'Article',
      headline: cleanTitle,
      description: article.excerpt,
      image: article.coverImage,
      datePublished: article.publishedAt,
      author: {
        '@type': 'Organization',
        name: 'みっけ！',
      },
    }
  ];

  if (article.rankings && article.rankings.length > 0) {
    jsonLdList.push({
      '@context': 'https://schema.org',
      '@type': 'ItemList',
      name: `${cleanTitle} ランキング`,
      itemListElement: article.rankings.map((prod: any, index: number) => ({
        '@type': 'ListItem',
        position: index + 1,
        name: prod.name,
        url: `https://www.mikke-style.com/articles/${slug}#${index + 1}`
      }))
    });
  }

  if (article.faq && article.faq.length > 0) {
    jsonLdList.push({
      '@context': 'https://schema.org',
      '@type': 'FAQPage',
      mainEntity: article.faq.map((item: any) => ({
        '@type': 'Question',
        name: item.question,
        acceptedAnswer: {
          '@type': 'Answer',
          text: item.answer
        }
      }))
    });
  }

  return (
    <>
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ 
          __html: JSON.stringify(jsonLdList.length === 1 ? jsonLdList[0] : jsonLdList) 
        }}
      />
      <article className="w-full pb-24 animate-fade-in-up bg-background s-article-page">
        
        <div className="container mx-auto max-w-3xl px-4 pt-8">

          {/* アイキャッチ画像 — 記事最上部・フル幅 */}
          <EyecatchImage slug={slug} alt={cleanTitle} />

          {/* 広告①〜④をランダム表示 */}
          <AdBanner type="small" />

          {/* Navigation (Breadcrumbs) */}
          <nav className="text-[10px] md:text-xs font-bold mb-6 flex items-center justify-center gap-2 text-muted" aria-label="パンくずリスト">
            <Link href="/" className="hover:text-primary transition-colors">ホーム</Link>
            <span className="text-primary/30" aria-hidden="true">&gt;</span>
            <Link href="/articles" className="hover:text-primary transition-colors">記事一覧</Link>
            {article.category && (
              <>
                <span className="text-primary/30" aria-hidden="true">&gt;</span>
                <span className="text-foreground" aria-current="page">{article.category}</span>
              </>
            )}
          </nav>
          
          {/* 🌸 Cute Article Hero */}
          <header className="bg-white rounded-[8px] p-6 md:p-10 cute-shadow border border-card-border mb-8 text-center relative overflow-hidden">
            <div className="absolute top-0 right-0 w-32 h-32 bg-primary/5 rounded-bl-[100px] pointer-events-none"></div>
            
            <div className="inline-block bg-primary/10 text-primary px-4 py-1.5 rounded-[4px] text-xs font-black mb-6">
              レビュー
            </div>
            
            <h1 className="article-title leading-snug mb-2 text-foreground flex flex-col items-center">
              {(() => {
                const parts = cleanTitle.split(/(?=【)/);
                if (parts.length > 1) {
                  const mainTitle = parts[0].trim();
                  const subTitleRaw = parts[1].trim();
                  
                  // Extract content within brackets e.g. "Mac miniと調和するモニター選び6選"
                  const subContent = subTitleRaw.replace(/[【】]/g, '');
                  
                  // Split "Mac miniと調和する" from "モニター選び6選"
                  const monitorSelectMatch = subContent.match(/(.*?)(モニター選び\d+選|選び\d+選|ガジェット\d+選|アイテム\d+選|文具\d+選|器具\d+選)(.*)/);
                  
                  if (monitorSelectMatch) {
                    const subPart1 = monitorSelectMatch[1].trim();
                    const subPart2 = `【${monitorSelectMatch[2].trim()}】`;
                    
                    return (
                      <>
                        <span className="block text-xl md:text-2xl lg:text-3xl font-black text-foreground mb-3 leading-normal">{mainTitle}</span>
                        <span className="block text-sm md:text-base lg:text-lg text-foreground/75 mb-1 font-bold leading-normal">{subPart1}</span>
                        <span className="block text-lg md:text-xl lg:text-2xl font-black text-primary">{subPart2}</span>
                      </>
                    );
                  }
                  
                  return (
                    <>
                      <span className="block text-xl md:text-2xl lg:text-3xl font-black text-foreground mb-2">{mainTitle}</span>
                      <span className="block text-lg md:text-xl lg:text-2xl font-bold text-primary">{subTitleRaw}</span>
                    </>
                  );
                }
                return <span className="text-xl md:text-2xl lg:text-3xl font-black">{cleanTitle}</span>;
              })()}
            </h1>
            
            <div className="flex items-center justify-center gap-2 mb-6 text-[10px] md:text-xs font-bold text-muted">
              <span>✍️ 著者: みっけ！編集部</span>
            </div>
            
            <time dateTime={article.publishedAt} className="text-[10px] md:text-xs font-bold text-muted block mb-6">
              🗓 {(() => {
                const d = new Date(article.publishedAt || "");
                return isNaN(d.getTime()) ? '' : d.toLocaleDateString('ja-JP');
              })()}
            </time>
            
            {article.excerpt && (
              <p className="text-sm md:text-base font-bold text-foreground bg-background rounded-[4px] p-4 inline-block text-left">
                💡 {article.excerpt}
              </p>
            )}
          </header>

          {/* 📝 Article Content Area */}
          <div className="bg-white rounded-[8px] p-6 md:p-10 cute-shadow border border-card-border mb-12">

            {/* 🏆 Ranking Table */}
            {article.rankings.length > 0 && (
              <RankingTable
                products={article.rankings}
                title={`${cleanTitle} ランキング`}
              />
            )}

            {article.content ? (() => {
              const content = article.content || "";
              const splitPattern = /(<h2[^>]*>.*?選び方のポイント.*?<\/h2>)/i;
              const parts = content.split(splitPattern);

              if (parts.length >= 2) {
                // parts[0] is content before heading
                // parts[1] is the heading itself
                // parts[2] is content after heading
                return (
                  <>
                    <div className="rich-text-container cute-html-content" dangerouslySetInnerHTML={{ __html: parts[0] }} />
                    <AdBanner type="small" />
                    <div className="rich-text-container cute-html-content" dangerouslySetInnerHTML={{ __html: parts.slice(1).join('') }} />
                  </>
                );
              }

              return <div className="rich-text-container cute-html-content" dangerouslySetInnerHTML={{ __html: content }} />;
            })() : article.body ? (
              <div className="rich-text-container cute-html-content">
                {documentToReactComponents(article.body)}
              </div>
            ) : null}
            
            {/* Share Section */}
            <ShareButtons
              url={`https://www.mikke-style.com/articles/${article.slug}`}
              title={cleanTitle}
              isGadget={cleanTitle.includes('ガジェット') || article.slug.includes('ガジェット')}
            />
          </div>

          {/* まとめセクションの直後（記事本文の最後）に広告⑤〜⑦をランダム表示 */}
          <AdBanner type="large" />

          {/* 🎀 Related Articles Section */}
          {relatedArticles.length > 0 && (
            <section className="mt-16">
              <h2 className="text-xl md:text-2xl font-black text-foreground mb-8 text-center flex items-center justify-center gap-2">
                <span className="text-primary">🌈</span> あわせて見たい記事
              </h2>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                {relatedArticles.map((rel) => {
                  const cleanRelTitle = rel.title.replace(/<br\s*\/?>/gi, '');
                  return (
                    <Link 
                      key={rel.slug} 
                      href={`/articles/${rel.slug}`}
                      className="group bg-white rounded-[8px] p-3 cute-shadow border border-card-border hover:-translate-y-1 transition-all duration-300"
                    >
                      <div className="aspect-[16/9] rounded-[4px] overflow-hidden mb-3 bg-primary/5 flex items-center justify-center">
                        {rel.coverImage ? (
                          <img src={rel.coverImage} alt={cleanRelTitle} loading="lazy" className="max-w-full max-h-full w-full h-full object-contain group-hover:scale-102 transition-transform duration-500" />
                        ) : (
                          <div className="w-full h-full flex items-center justify-center text-2xl">🎀</div>
                        )}
                      </div>
                      <h3 className="text-sm font-black text-foreground group-hover:text-primary transition-colors line-clamp-2 leading-snug">{cleanRelTitle}</h3>
                    </Link>
                  );
                })}
              </div>
            </section>
          )}

        </div>
      </article>
    </>
  );
}
