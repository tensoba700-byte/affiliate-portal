import { getAllArticles, getArticleBySlug } from '@/src/lib/api';
import Link from 'next/link';
import Image from 'next/image';

export const revalidate = 3600; // ISR cache revalidation hourly

interface PageProps {
  searchParams: Promise<{ category?: string; sort?: string; page?: string }>;
}

const categoryMap: { [key: string]: { key: string; name: string; emoji: string } } = {
  balm: { key: 'balm', name: 'クレンジングバーム', emoji: '🧴' },
  toner: { key: 'toner', name: '化粧水', emoji: '💧' },
  oil: { key: 'oil', name: 'クレンジングオイル', emoji: '🧪' },
  gel: { key: 'gel', name: 'クレンジングジェル', emoji: '🧼' },
  booster: { key: 'booster', name: '導入美容液', emoji: '🧪' },
  lip: { key: 'lip', name: 'リップ美容液', emoji: '💄' },
  cream: { key: 'cream', name: '保湿クリーム', emoji: '🧴' },
  emulsion: { key: 'emulsion', name: '乳液', emoji: '🧴' },
  mask: { key: 'mask', name: 'フェイスパック', emoji: '🎭' },
  cleanser: { key: 'cleanser', name: '洗顔料', emoji: '🧼' },
  sunscreen: { key: 'sunscreen', name: '日焼け止め', emoji: '☀️' },
  serum: { key: 'serum', name: '美容液', emoji: '🧪' },
  shampoo: { key: 'shampoo', name: 'シャンプー', emoji: '🧴' },
  hair: { key: 'hair', name: 'ヘアケア', emoji: '💇' },
  eyeliner: { key: 'eyeliner', name: 'アイライナー', emoji: '👁️' },
  handcream: { key: 'handcream', name: 'ハンドクリーム', emoji: '🖐️' },
};

function detectCategory(slug: string, title: string) {
  const s = slug.toLowerCase();
  const t = title.toLowerCase();
  
  if (s.includes('cleansing-balm') || t.includes('クレンジングバーム')) {
    return categoryMap.balm;
  }
  if (s.includes('toner') || t.includes('化粧水')) {
    return categoryMap.toner;
  }
  if (s.includes('cleansing-oil') || t.includes('クレンジングオイル')) {
    return categoryMap.oil;
  }
  if (s.includes('cleansing-gel') || t.includes('クレンジングジェル')) {
    return categoryMap.gel;
  }
  if (s.includes('booster') || t.includes('導入美容液') || t.includes('ブースター')) {
    return categoryMap.booster;
  }
  if (s.includes('lip-serum') || t.includes('リップ美容液')) {
    return categoryMap.lip;
  }
  if (s.includes('face-cream') || t.includes('保湿クリーム') || t.includes('フェイスクリーム')) {
    return categoryMap.cream;
  }
  if (s.includes('emulsion') || t.includes('乳液')) {
    return categoryMap.emulsion;
  }
  if (s.includes('face-mask') || s.includes('sheet-mask') || s.includes('daily-pack') || t.includes('フェイスパック') || t.includes('シートマスク') || t.includes('パック')) {
    return categoryMap.mask;
  }
  if (s.includes('cleanser') || s.includes('face-wash') || t.includes('洗顔')) {
    return categoryMap.cleanser;
  }
  if (s.includes('sunscreen') || t.includes('日焼け止め')) {
    return categoryMap.sunscreen;
  }
  if (s.includes('serum') || t.includes('美容液')) {
    return categoryMap.serum;
  }
  if (s.includes('shampoo') || t.includes('シャンプー')) {
    return categoryMap.shampoo;
  }
  if (s.includes('hair') || t.includes('ヘアケア') || t.includes('トリートメント')) {
    return categoryMap.hair;
  }
  if (s.includes('eyeliner') || t.includes('アイライナー')) {
    return categoryMap.eyeliner;
  }
  if (s.includes('hand-cream') || t.includes('ハンドクリーム')) {
    return categoryMap.handcream;
  }
  
  return { key: 'other', name: 'その他', emoji: '🛍️' };
}

export default async function ProductsPage({ searchParams }: PageProps) {
  const resolvedParams = await searchParams;
  const currentCategory = resolvedParams.category || 'all';
  const currentSort = resolvedParams.sort || 'score';
  const currentPage = parseInt(resolvedParams.page || '1', 10);
  const limit = 24; // 1ページあたり24商品

  // 1. 公開済みの全記事から商品を動的に集約
  const allArticles = await getAllArticles();
  
  // 各記事を個別に詳細ロードしてランキング（商品）を抽出
  const articlesWithDetails = await Promise.all(
    allArticles.map(async (art) => {
      try {
        const detail = await getArticleBySlug(art.slug);
        return detail;
      } catch (err) {
        console.error(`Failed to load article detail for ${art.slug}:`, err);
        return null;
      }
    })
  );

  const activeArticles = articlesWithDetails.filter((art): art is NonNullable<typeof art> => {
    return art !== null && art.rankings && art.rankings.length > 0;
  });

  const allProducts = activeArticles.flatMap(article => {
    const cat = detectCategory(article.slug, article.title);
    return article.rankings.map(p => ({
      ...p,
      categoryKey: cat.key,
      categoryName: cat.name,
      articleSlug: article.slug,
    }));
  });

  // 2. カテゴリごとの件数を集計してタブ用に動的生成
  const categoryCounts: { [key: string]: { name: string; count: number } } = {};
  allProducts.forEach(p => {
    if (!categoryCounts[p.categoryKey]) {
      categoryCounts[p.categoryKey] = { name: p.categoryName, count: 0 };
    }
    categoryCounts[p.categoryKey].count += 1;
  });

  const categoryKeysOrder = Object.keys(categoryMap);
  const categories = Object.keys(categoryCounts)
    .map(key => ({
      key,
      name: categoryCounts[key].name,
      count: categoryCounts[key].count,
    }))
    .sort((a, b) => {
      const idxA = categoryKeysOrder.indexOf(a.key);
      const idxB = categoryKeysOrder.indexOf(b.key);
      const valA = idxA === -1 ? 999 : idxA;
      const valB = idxB === -1 ? 999 : idxB;
      return valA - valB;
    });

  let products = [...allProducts];

  // 3. フィルタリング
  if (currentCategory !== 'all') {
    products = products.filter(p => p.categoryKey === currentCategory);
  }

  // 4. ソート
  if (currentSort === 'score') {
    products.sort((a, b) => b.score - a.score);
  } else if (currentSort === 'price_asc') {
    const getPriceVal = (priceStr?: string) => {
      if (!priceStr) return 999999;
      const num = parseInt(priceStr.replace(/[^0-9]/g, ''), 10);
      return isNaN(num) ? 999999 : num;
    };
    products.sort((a, b) => {
      const priceA = getPriceVal(a.rakuten?.price || a.amazon?.price);
      const priceB = getPriceVal(b.rakuten?.price || b.amazon?.price);
      return priceA - priceB;
    });
  }

  // 5. ページネーション
  const totalProducts = products.length;
  const totalPages = Math.ceil(totalProducts / limit);
  const page = Math.max(1, Math.min(currentPage, totalPages || 1));
  const pagedProducts = products.slice((page - 1) * limit, page * limit);

  const getCategoryEmoji = (key: string) => {
    return categoryMap[key]?.emoji || '🛍️';
  };

  return (
    <div className="s-prod-page">
      {/* Breadcrumbs */}
      <nav className="s-breadcrumb" style={{ marginBottom: 24, justifyContent: 'center' }}>
        <Link href="/">HOME</Link>
        <span className="s-breadcrumb-sep">/</span>
        <span aria-current="page">VERIFIED PRODUCTS</span>
      </nav>

      {/* Header */}
      <header className="s-prod-header">
        <h1 className="s-prod-title">Verified Products</h1>
        <p className="s-prod-subtitle">ガチ検証で厳選した本音コスメ図鑑</p>
      </header>

      {/* Controls Bar */}
      <div className="s-prod-bar">
        {/* Category Tabs */}
        <div className="s-prod-tabs">
          <Link 
            href={`/products?category=all&sort=${currentSort}`} 
            className={`s-prod-tab ${currentCategory === 'all' ? 's-prod-tab-active' : ''}`}
          >
            すべて ({allProducts.length})
          </Link>
          {categories.map(cat => (
            <Link 
              key={cat.key}
              href={`/products?category=${cat.key}&sort=${currentSort}`} 
              className={`s-prod-tab ${currentCategory === cat.key ? 's-prod-tab-active' : ''}`}
            >
              {cat.name} ({cat.count})
            </Link>
          ))}
        </div>

        {/* Sort selector */}
        <div className="s-prod-sort-wrap">
          <span className="s-prod-sort-label">並び替え:</span>
          <div className="s-prod-sort-select-btn">
            <Link 
              href={`/products?category=${currentCategory}&sort=score`}
              className={`s-prod-sort-btn ${currentSort === 'score' ? 's-prod-sort-btn-active' : ''}`}
            >
              ⭐ おすすめ順
            </Link>
            <Link 
              href={`/products?category=${currentCategory}&sort=price_asc`}
              className={`s-prod-sort-btn ${currentSort === 'price_asc' ? 's-prod-sort-btn-active' : ''}`}
            >
              ¥ 安い順
            </Link>
          </div>
        </div>
      </div>

      {/* Products Grid */}
      <div className="s-prod-grid">
        {pagedProducts.map((prod) => {
          const mainPrice = prod.rakuten?.price || prod.amazon?.price || '価格を見る';
          return (
            <div key={`${prod.categoryKey}-${prod.rank}-${prod.name}`} className="s-prod-card">
              <div className="s-prod-badge-wrap">
                <span className="s-prod-rank-badge">🏆 第{prod.rank}位</span>
                <span className="s-prod-cat-badge">
                  {getCategoryEmoji(prod.categoryKey)} {prod.categoryName}
                </span>
              </div>

              {/* Product Image */}
              <div className="s-prod-img-box">
                {prod.imageUrl ? (
                  <Image
                    src={prod.imageUrl}
                    alt={prod.name}
                    width={200}
                    height={200}
                    className="s-prod-img"
                    referrerPolicy="no-referrer"
                  />
                ) : (
                  <span style={{ fontSize: '32px' }}>🛍️</span>
                )}
              </div>

              {/* Product Info */}
              <div className="s-prod-info">
                <div className="s-prod-name-wrap">
                  <h3 className="s-prod-name">{prod.name}</h3>
                </div>
                <div className="s-prod-score-row">
                  <span className="s-prod-star">⭐</span>
                  <span className="s-prod-score-num">{prod.score.toFixed(2)}</span>
                </div>
                
                {/* Pros list */}
                {prod.pros && prod.pros.length > 0 && (
                  <div className="s-prod-pros">
                    {prod.pros.slice(0, 2).map((pro, idx) => (
                      <div key={idx} className="s-prod-pro-item">
                        <span>✅</span>
                        <span>{pro}</span>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {/* Price row */}
              <div className="s-prod-price-row">
                <span className="s-prod-price-label">取得価格:</span>
                <span className="s-prod-price-val">{mainPrice}</span>
              </div>

              <div className="s-prod-buttons">
                <a 
                  href={prod.amazon?.url || '#'} 
                  target="_blank" 
                  rel="noopener noreferrer nofollow sponsored" 
                  className="s-prod-btn-amz"
                >
                  <Image
                    src="https://www.amazon.co.jp/favicon.ico"
                    className="s-prod-btn-icon"
                    alt=""
                    width={16}
                    height={16}
                  /> Amazon
                </a>
                <a 
                  href={prod.rakuten?.url || '#'} 
                  target="_blank" 
                  rel="noopener noreferrer nofollow sponsored" 
                  className="s-prod-btn-rak"
                >
                  <Image
                    src="https://www.rakuten.co.jp/favicon.ico"
                    className="s-prod-btn-icon"
                    alt=""
                    width={16}
                    height={16}
                  /> 楽天市場
                </a>
              </div>

              <Link href={`/articles/${prod.articleSlug}`} className="s-prod-report-btn">
                📄 この記事で紹介
              </Link>
            </div>
          );
        })}
      </div>

      {/* Pagination Controls */}
      {totalPages > 1 && (
        <div className="s-pagination">
          {page > 1 && (
            <Link 
              href={`/products?category=${currentCategory}&sort=${currentSort}&page=${page - 1}`} 
              className="s-pagination-btn"
            >
              &larr; 前へ
            </Link>
          )}
          {Array.from({ length: totalPages }).map((_, idx) => {
            const pageNum = idx + 1;
            return (
              <Link
                key={pageNum}
                href={`/products?category=${currentCategory}&sort=${currentSort}&page=${pageNum}`}
                className={`s-pagination-num ${page === pageNum ? 's-pagination-num-active' : ''}`}
              >
                {pageNum}
              </Link>
            );
          })}
          {page < totalPages && (
            <Link 
              href={`/products?category=${currentCategory}&sort=${currentSort}&page=${page + 1}`} 
              className="s-pagination-btn"
            >
              次へ &rarr;
            </Link>
          )}
        </div>
      )}
    </div>
  );
}
