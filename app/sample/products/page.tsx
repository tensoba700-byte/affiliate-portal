import { getArticleBySlug } from '@/src/lib/api';
import Link from 'next/link';

interface PageProps {
  searchParams: Promise<{ category?: string; sort?: string }>;
}

export default async function SampleProductsPage({ searchParams }: PageProps) {
  const resolvedParams = await searchParams;
  const currentCategory = resolvedParams.category || 'all';
  const currentSort = resolvedParams.sort || 'score';

  // 1. マークダウンから直接データを取得
  const balmArticle = await getArticleBySlug('20260609-cleansing-balm');
  const tonerArticle = await getArticleBySlug('20260608-toner');

  // カテゴリ分けと元記事へのリンク情報をマッピング
  const balmProducts = balmArticle 
    ? balmArticle.rankings.map(p => ({ 
        ...p, 
        categoryKey: 'balm', 
        categoryName: 'クレンジングバーム', 
        articleSlug: '20260609-cleansing-balm' 
      })) 
    : [];
  
  const tonerProducts = tonerArticle 
    ? tonerArticle.rankings.map(p => ({ 
        ...p, 
        categoryKey: 'toner', 
        categoryName: '化粧水', 
        articleSlug: '20260608-toner' 
      })) 
    : [];

  let products = [...balmProducts, ...tonerProducts];

  // 2. フィルタリング
  if (currentCategory !== 'all') {
    products = products.filter(p => p.categoryKey === currentCategory);
  }

  // 3. ソート
  if (currentSort === 'score') {
    // 評価スコアが高い順
    products.sort((a, b) => b.score - a.score);
  } else if (currentSort === 'price_asc') {
    // 安い順
    const getPriceVal = (priceStr?: string) => {
      if (!priceStr) return 999999;
      // 価格の表記から数値を抽出（例: '3,960円' または '¥3,960'）
      const num = parseInt(priceStr.replace(/[^0-9]/g, ''), 10);
      return isNaN(num) ? 999999 : num;
    };
    products.sort((a, b) => {
      const priceA = getPriceVal(a.rakuten?.price || a.amazon?.price);
      const priceB = getPriceVal(b.rakuten?.price || b.amazon?.price);
      return priceA - priceB;
    });
  }

  // カテゴリごとのアイコン
  const getCategoryEmoji = (key: string) => {
    return key === 'balm' ? '🧴' : '💧';
  };

  return (
    <div className="s-prod-page">
      {/* Breadcrumbs */}
      <nav className="s-breadcrumb" style={{ marginBottom: 24, justifyContent: 'center' }}>
        <Link href="/sample">HOME</Link>
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
            href={`/sample/products?category=all&sort=${currentSort}`} 
            className={`s-prod-tab ${currentCategory === 'all' ? 's-prod-tab-active' : ''}`}
          >
            すべて ({balmProducts.length + tonerProducts.length})
          </Link>
          <Link 
            href={`/sample/products?category=balm&sort=${currentSort}`} 
            className={`s-prod-tab ${currentCategory === 'balm' ? 's-prod-tab-active' : ''}`}
          >
            🧴 クレンジングバーム ({balmProducts.length})
          </Link>
          <Link 
            href={`/sample/products?category=toner&sort=${currentSort}`} 
            className={`s-prod-tab ${currentCategory === 'toner' ? 's-prod-tab-active' : ''}`}
          >
            💧 化粧水 ({tonerProducts.length})
          </Link>
        </div>

        {/* Sort selector using Links */}
        <div className="s-prod-sort-wrap">
          <span className="s-prod-sort-label">並び替え:</span>
          <div className="s-prod-sort-select-btn">
            <Link 
              href={`/sample/products?category=${currentCategory}&sort=score`}
              className={`s-prod-sort-btn ${currentSort === 'score' ? 's-prod-sort-btn-active' : ''}`}
            >
              ⭐ おすすめ順
            </Link>
            <Link 
              href={`/sample/products?category=${currentCategory}&sort=price_asc`}
              className={`s-prod-sort-btn ${currentSort === 'price_asc' ? 's-prod-sort-btn-active' : ''}`}
            >
              ¥ 安い順
            </Link>
          </div>
        </div>
      </div>

      {/* Products Grid */}
      <div className="s-prod-grid">
        {products.map((prod) => {
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
                  <img src={prod.imageUrl} alt={prod.name} className="s-prod-img" referrerPolicy="no-referrer" />
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

              {/* Action Buttons */}
              <div className="s-prod-buttons">
                <a 
                  href={prod.amazon?.url || '#'} 
                  target="_blank" 
                  rel="noopener noreferrer nofollow sponsored" 
                  className="s-prod-btn-amz"
                >
                  <img src="https://www.amazon.co.jp/favicon.ico" className="s-prod-btn-icon" alt="" /> Amazon
                </a>
                <a 
                  href={prod.rakuten?.url || '#'} 
                  target="_blank" 
                  rel="noopener noreferrer nofollow sponsored" 
                  className="s-prod-btn-rak"
                >
                  <img src="https://www.rakuten.co.jp/favicon.ico" className="s-prod-btn-icon" alt="" /> 楽天市場
                </a>
              </div>

              <Link href={`/sample/articles/${prod.articleSlug}`} className="s-prod-report-btn">
                📄 この記事で紹介
              </Link>
            </div>

          );
        })}
      </div>
    </div>
  );
}
