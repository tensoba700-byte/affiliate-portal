/**
 * RankingTable — my-best.com 風の商品比較ランキング表
 *
 * 使用例:
 * -------
 * import RankingTable from "@/src/components/RankingTable";
 *
 * const products: Product[] = [
 *   {
 *     rank: 1,
 *     brand: "COSRX",
 *     name: "アドバンスドスネイルムチン96パワーエッセンス",
 *     imageUrl: "https://example.com/img.jpg",
 *     score: 4.79,
 *     amazon:  { price: "¥1,980", url: "https://amazon.co.jp/" },
 *     yahoo:   { price: "¥2,100", url: "https://shopping.yahoo.co.jp/" },
 *     rakuten: { price: "¥1,950", url: "https://rakuten.co.jp/" },
 *   },
 *   // ... 最大6件
 * ];
 *
 * <RankingTable products={products} title="スキンケアおすすめランキング" />
 */

"use client";
import React, { useState } from "react";

export type Product = {
  rank: number;
  brand: string;
  name: string;
  imageUrl: string;
  score: number;
  amazon?: { price: string; url: string };
  yahoo?: { price: string; url: string };
  rakuten?: { price: string; url: string };
};

type Tab = "recommend" | "cospa" | "popular";

const TABS: { key: Tab; label: string }[] = [
  { key: "recommend", label: "おすすめ順" },
  { key: "cospa",     label: "コスパ順"   },
  { key: "popular",   label: "人気順"     },
];

/** ランクバッジ — 金・銀・銅 */
function RankBadge({ rank }: { rank: number }) {
  const top3: Record<number, { bg: string; label: string }> = {
    1: { bg: 'linear-gradient(135deg, #FFD700, #FF8C00)', label: '1st' },
    2: { bg: 'linear-gradient(135deg, #D8D8D8, #9A9A9A)', label: '2nd' },
    3: { bg: 'linear-gradient(135deg, #CE7B3A, #8B4513)', label: '3rd' },
  };

  if (top3[rank]) {
    return (
      <div
        className="flex items-center justify-center flex-shrink-0"
        style={{
          width: 44, height: 44, borderRadius: '50%',
          background: top3[rank].bg,
          color: '#FFFFFF',
          fontWeight: 900, fontSize: 13,
          boxShadow: '0 3px 10px rgba(0,0,0,0.25)',
          letterSpacing: '0.5px',
        }}
      >
        {top3[rank].label}
      </div>
    );
  }

  return (
    <div
      className="flex items-center justify-center flex-shrink-0"
      style={{
        width: 40, height: 40, borderRadius: '50%',
        background: '#444',
        color: '#FFFFFF',
        fontWeight: 900, fontSize: 11,
        boxShadow: '0 2px 6px rgba(0,0,0,0.18)',
      }}
    >
      {rank}位
    </div>
  );
}

/** 星マーク */
function Stars({ score }: { score: number }) {
  const full  = Math.floor(score);
  const half  = score % 1 >= 0.4;
  const empty = 5 - full - (half ? 1 : 0);
  return (
    <span className="text-sm leading-none">
      <span style={{ color: "#F9A825" }}>{"★".repeat(full)}{half ? "½" : ""}</span>
      <span style={{ color: "#E0E0E0" }}>{"★".repeat(empty)}</span>
    </span>
  );
}

/** 購入ボタン */
function BuyButton({
  label, price, url, bg, textColor = '#FFFFFF', iconUrl,
}: {
  label: string; price: string; url: string; bg: string; textColor?: string; iconUrl: string;
}) {
  if (!url && !price) return null;
  return (
    <a
      href={url || "#"}
      target="_blank"
      rel="noopener noreferrer"
      className="flex items-center gap-2 px-3 py-2 font-bold transition-all whitespace-nowrap active:scale-95"
      style={{
        background: bg,
        color: textColor,
        minHeight: '42px',
        fontSize: '11px',
        borderRadius: '10px',
        boxShadow: '0 3px 10px rgba(0,0,0,0.2)',
        textDecoration: 'none',
        minWidth: '80px',
        filter: 'brightness(1)',
      }}
      onMouseEnter={e => (e.currentTarget.style.filter = 'brightness(0.88)')}
      onMouseLeave={e => (e.currentTarget.style.filter = 'brightness(1)')}
    >
      {/* ロゴアイコン */}
      <span className="rounded p-0.5 flex-shrink-0 flex items-center justify-center" style={{ background: 'rgba(255,255,255,0.25)' }}>
        <img src={iconUrl} alt={label} width={14} height={14} className="object-contain" style={{ borderRadius: '2px' }} />
      </span>
      {/* テキスト */}
      <span className="flex flex-col leading-tight text-left">
        <span style={{ fontWeight: 700 }}>{label}で見る</span>
        {price && <span style={{ fontSize: '10px', opacity: 0.9 }}>{price}</span>}
      </span>
    </a>
  );
}

type Props = {
  products: Product[];
  title?: string;
  rankingAd?: React.ReactNode;
};

export default function RankingTable({ products, title, rankingAd }: Props) {
  const [activeTab, setActiveTab] = useState<Tab>("recommend");

  // Sorting logic based on activeTab
  const sortedProducts = [...products].sort((a, b) => {
    if (activeTab === "recommend") {
      return b.score - a.score;
    }
    if (activeTab === "cospa") {
      // Logic: Lower (Price / Score) is better
      const getPriceValue = (p: Product) => {
        const priceStr = p.amazon?.price || p.rakuten?.price || p.yahoo?.price || "0";
        return parseInt(priceStr.replace(/[^0-9]/g, ""), 10) || 1000000; // default high price if missing
      };
      const valA = getPriceValue(a) / (a.score || 1);
      const valB = getPriceValue(b) / (b.score || 1);
      return valA - valB;
    }
    if (activeTab === "popular") {
      return a.rank - b.rank; // Original rank
    }
    return 0;
  });

  const displayed = sortedProducts.slice(0, 6);

  /* パステルピンク系トークン */
  const C = {
    headerBg: "#FFF0F5",
    headerText: "#b85c7a",
    border: "#F8D7E3",
    tabActiveBorder: "#e06a8c",
    tabActiveText: "#e06a8c",
    tabInactiveText: "#bbb",
    rowHover: "#FFF7FA",
    colHeaderBg: "#FFF0F5",
    colHeaderText: "#b85c7a",
    scoreColor: "#e06a8c",
    footerBg: "#FFF0F5",
    footerText: "#c49aaa",
  };

  return (
    <div
      className="w-full my-8 rounded-2xl overflow-hidden"
      style={{ border: `1.5px solid ${C.border}`, boxShadow: "0 4px 24px rgba(224,106,140,.08)" }}
    >
      {/* ヘッダー */}
      {title && (
        <div
          className="px-5 py-3 font-black text-sm flex items-center gap-2"
          style={{ background: C.headerBg, color: C.headerText, borderBottom: `1.5px solid ${C.border}` }}
        >
          🏆 {title}
        </div>
      )}

      {/* タブ */}
      <div
        className="flex"
        style={{ background: "#fff", borderBottom: `1.5px solid ${C.border}` }}
      >
        {TABS.map((tab) => {
          const active = activeTab === tab.key;
          return (
            <button
              key={tab.key}
              onClick={() => setActiveTab(tab.key)}
              className="flex-1 py-2.5 text-xs font-black transition-all"
              style={{
                color: active ? C.tabActiveText : C.tabInactiveText,
                borderBottom: active ? `2.5px solid ${C.tabActiveBorder}` : "2.5px solid transparent",
                background: active ? "#fff" : "transparent",
              }}
            >
              {tab.label}
            </button>
          );
        })}
      </div>

      {/* テーブルヘッダー（PCのみ） */}
      <div
        className="hidden md:grid grid-cols-[2.5rem_6.5rem_1fr_5rem_auto] gap-3 items-center px-5 py-2.5 text-[11px] font-black"
        style={{ background: C.colHeaderBg, color: C.colHeaderText, borderBottom: `1px solid ${C.border}` }}
      >
        <span>順位</span>
        <span className="text-center">画像</span>
        <span>商品名</span>
        <span className="text-center">スコア</span>
        <span className="text-center">購入ページへ</span>
      </div>

      {/* 商品行 */}
      <div className="divide-y" style={{ borderColor: C.border }}>
        {displayed.map((p, idx) => (
          <React.Fragment key={p.name}>
            <div
              className="grid grid-cols-1 md:grid-cols-[2.5rem_6.5rem_1fr_5rem_auto] gap-3 items-center px-4 py-4 bg-white transition-colors"
              onMouseEnter={e => (e.currentTarget.style.background = C.rowHover)}
              onMouseLeave={e => (e.currentTarget.style.background = "#fff")}
            >
              {/* バッジ — ソート後の表示順を反映 */}
              <div className="flex items-center gap-3 md:block">
                <RankBadge rank={idx + 1} />
                <div className="md:hidden flex-1">
                  {p.brand && <p className="text-[10px] font-bold" style={{ color: "#bbb" }}>{p.brand}</p>}
                  <p className="text-sm font-black" style={{ color: C.scoreColor }}>{p.name}</p>
                </div>
              </div>

              {/* 画像 */}
              <div className="flex items-center justify-center">
                {p.imageUrl ? (
                  <div
                    className="w-20 h-20 md:w-24 md:h-24 rounded-[14px] overflow-hidden bg-white flex items-center justify-center flex-shrink-0"
                    style={{ boxShadow: '0 4px 16px rgba(0,0,0,0.12)', borderRadius: '14px' }}
                  >
                    <img
                      src={p.imageUrl}
                      alt={p.name}
                      className="object-contain w-full h-full"
                      style={{ borderRadius: '14px', mixBlendMode: 'multiply' }}
                    />
                  </div>
                ) : (
                  <div
                    className="w-20 h-20 md:w-24 md:h-24 rounded-[14px] overflow-hidden bg-white flex items-center justify-center flex-shrink-0"
                    style={{ boxShadow: '0 4px 16px rgba(0,0,0,0.12)', borderRadius: '14px', background: C.headerBg }}
                  >
                    🎀
                  </div>
                )}
              </div>

              {/* 商品名（PCのみ - モバイルはバッジ横に表示） */}
              <div className="hidden md:block">
                {p.brand && <p className="text-[10px] font-bold mb-0.5" style={{ color: "#bbb" }}>{p.brand}</p>}
                <p className="text-sm font-black leading-snug underline underline-offset-2" style={{ color: C.scoreColor }}>
                  {p.name}
                </p>
              </div>

              {/* スコア */}
              <div className="flex md:flex-col items-center gap-1">
                <span className="text-base font-black" style={{ color: C.scoreColor }}>{p.score.toFixed(2)}</span>
                <Stars score={p.score} />
              </div>

              {/* 購入ボタン: Amazon → 楽天 → Yahoo の順 */}
              <div className="flex flex-wrap gap-2">
                {p.amazon && (
                  <BuyButton
                    label="Amazon"
                    price={p.amazon.price}
                    url={p.amazon.url}
                    bg="#FF9900"
                    textColor="#111111"
                    iconUrl="https://www.amazon.co.jp/favicon.ico"
                  />
                )}
                {p.rakuten && (
                  <BuyButton
                    label="楽天市場"
                    price={p.rakuten.price}
                    url={p.rakuten.url}
                    bg="#BF0000"
                    textColor="#FFFFFF"
                    iconUrl="https://www.rakuten.co.jp/favicon.ico"
                  />
                )}
                {p.yahoo && (
                  <BuyButton
                    label="Yahoo!"
                    price={p.yahoo.price}
                    url={p.yahoo.url}
                    bg="#FF0033"
                    textColor="#FFFFFF"
                    iconUrl="https://shopping.yahoo.co.jp/favicon.ico"
                  />
                )}
              </div>
            </div>
            {/* 3位の後に広告を挿入 */}
            {idx === 2 && rankingAd && (
              <div className="px-4 py-2 border-t" style={{ borderColor: C.border }}>
                {rankingAd}
              </div>
            )}
          </React.Fragment>
        ))}
      </div>

      {/* フッター */}
      <div
        className="px-5 py-2.5 text-[10px] font-bold text-right"
        style={{ background: C.footerBg, color: C.footerText, borderTop: `1px solid ${C.border}` }}
      >
        ※ 価格はリンク先の商品ページでご確認ください。
      </div>
    </div>
  );
}
