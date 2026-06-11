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
  pros?: string[];
  cons?: string[];
  description?: string;
  features?: string[];
};

type Tab = "recommend" | "cospa" | "popular";

const TABS: { key: Tab; label: string; icon: string }[] = [
  { key: "recommend", label: "おすすめ順", icon: "👑" },
  { key: "cospa",     label: "コスパ順",   icon: "💎" },
  { key: "popular",   label: "人気順",     icon: "🔥" },
];

/** ランクバッジ — 金・銀・銅 */
function RankBadge({ rank }: { rank: number }) {
  const top3: Record<number, { bg: string; border: string; color: string; label: string; shadow: string }> = {
    1: { 
      bg: 'linear-gradient(135deg, #FFD700, #FFA500)', 
      border: '#FFF3A7', 
      color: '#FFFFFF', 
      label: '1st',
      shadow: 'rgba(255, 165, 0, 0.4)'
    },
    2: { 
      bg: 'linear-gradient(135deg, #E0E0E0, #B0B0B0)', 
      border: '#FFFFFF', 
      color: '#FFFFFF', 
      label: '2nd',
      shadow: 'rgba(176, 176, 176, 0.3)'
    },
    3: { 
      bg: 'linear-gradient(135deg, #CD7F32, #A0522D)', 
      border: '#FFE4C4', 
      color: '#FFFFFF', 
      label: '3rd',
      shadow: 'rgba(160, 82, 45, 0.3)'
    },
  };

  if (top3[rank]) {
    return (
      <div
        className="flex items-center justify-center flex-shrink-0 relative overflow-hidden transition-transform duration-300 group-hover:scale-110"
        style={{
          width: 42, height: 42, borderRadius: '14px',
          background: top3[rank].bg,
          color: top3[rank].color,
          fontWeight: 900, fontSize: 12,
          boxShadow: `0 3px 10px ${top3[rank].shadow}, inset 0 1.5px 1.5px rgba(255,255,255,0.4)`,
          border: `1.5px solid ${top3[rank].border}`,
          letterSpacing: '0.5px',
        }}
      >
        <span className="relative z-10">{top3[rank].label}</span>
        <div className="absolute top-0 left-[-50%] w-[200%] h-full bg-white/20 rotate-45 translate-y-[-70%] animate-pulse"></div>
      </div>
    );
  }

  return (
    <div
      className="flex items-center justify-center flex-shrink-0"
      style={{
        width: 36, height: 36, borderRadius: '10px',
        background: '#FAF0F4',
        color: '#b85c7a',
        fontWeight: 900, fontSize: 12,
        border: '1px solid #F8D7E3',
        boxShadow: '0 2px 4px rgba(184,92,122,0.04)',
      }}
    >
      {rank}
    </div>
  );
}

/** 星マーク */
function Stars({ score }: { score: number }) {
  const full  = Math.floor(score);
  const half  = score % 1 >= 0.4;
  const empty = 5 - full - (half ? 1 : 0);
  return (
    <span className="text-xs leading-none flex gap-0.5 justify-center">
      {"★".repeat(full).split("").map((s, i) => (
        <span key={`f-${i}`} style={{ color: "#FFB300" }} className="drop-shadow-[0_1px_1px_rgba(255,179,0,0.2)]">★</span>
      ))}
      {half && <span style={{ color: "#FFB300" }} className="drop-shadow-[0_1px_1px_rgba(255,179,0,0.2)]">½</span>}
      {"☆".repeat(empty).split("").map((s, i) => (
        <span key={`e-${i}`} style={{ color: "#E0E0E0" }}>★</span>
      ))}
    </span>
  );
}

/** 購入ボタン */
function BuyButton({
  label, price, url, bg, textColor = '#FFFFFF', iconUrl, hoverBg, shortLabel,
}: {
  label: string; price: string; url: string; bg: string; textColor?: string; iconUrl: string; hoverBg: string; shortLabel: string;
}) {
  if (!url && !price) return null;
  const [hovered, setHovered] = useState(false);

  return (
    <a
      href={url || "#"}
      target="_blank"
      rel="noopener noreferrer nofollow sponsored"
      className="s-buy-button flex items-center justify-center md:justify-between gap-1.5 md:gap-3 px-1.5 md:px-4 py-2 md:py-2.5 font-black transition-all duration-300 rounded-xl shadow-sm hover:shadow-md border border-black/5 flex-1 md:flex-initial"
      style={{
        background: hovered ? hoverBg : bg,
        color: textColor,
        minHeight: '36px',
        fontSize: '11px',
        textDecoration: 'none',
        transform: hovered ? 'translateY(-2px) scale(1.03)' : 'translateY(0) scale(1)',
        boxShadow: hovered ? '0 8px 20px rgba(0,0,0,0.12)' : '0 2px 4px rgba(0,0,0,0.05)',
      }}
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
    >
      <div className="flex items-center gap-1 md:gap-2">
        <span className="rounded-md md:rounded-lg p-0.5 md:p-1 flex-shrink-0 flex items-center justify-center bg-white/20">
          <img src={iconUrl} alt={label} width={12} height={12} className="object-contain md:w-3.5 md:h-3.5" />
        </span>
        <span className="flex flex-col leading-tight text-left">
          <span className="md:hidden font-black text-[10px] tracking-tight">{shortLabel}</span>
          {price && <span className="md:hidden text-[9px] font-bold opacity-90 leading-none">{price}</span>}
          <span className="hidden md:inline font-black text-[11px]">{label === 'Amazon' ? 'Amazon で購入' : `${label}で購入`}</span>
          {price && <span className="hidden md:inline text-[11px] font-black tracking-wider">{price}</span>}
        </span>
      </div>
      <svg className="hidden md:block w-3.5 h-3.5 opacity-70 transition-transform duration-300" style={{ transform: hovered ? 'translateX(2px)' : 'none' }} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={3}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M9 5l7 7-7 7" />
      </svg>
    </a>
  );
}

type Props = {
  products: Product[];
  title?: string;
};

export default function RankingTable({ products, title }: Props) {
  const [activeTab, setActiveTab] = useState<Tab>("recommend");

  // Sorting logic
  const sortedProducts = [...products].sort((a, b) => {
    if (activeTab === "recommend") {
      return a.rank - b.rank;
    }
    if (activeTab === "cospa") {
      const getPriceValue = (p: Product) => {
        const prices = [p.amazon?.price, p.rakuten?.price, p.yahoo?.price];
        for (const price of prices) {
          if (!price) continue;
          const cleaned = price.replace(/[^0-9]/g, "");
          if (cleaned.length > 0) {
            const num = parseInt(cleaned, 10);
            if (num > 0) return num;
          }
        }
        return 1000000;
      };
      const valA = getPriceValue(a) / (a.score || 1);
      const valB = getPriceValue(b) / (b.score || 1);
      return valA - valB;
    }
    if (activeTab === "popular") {
      return a.rank - b.rank;
    }
    return 0;
  });

  const displayed = sortedProducts.slice(0, 6);

  /* パステルピンク系キュート＆プレミアムカラー */
  const C = {
    headerBg: "linear-gradient(135deg, #FFF0F5, #FFE4E1)",
    headerText: "#b85c7a",
    border: "#F8D7E3",
    tabActiveBg: "#e06a8c",
    tabActiveText: "#FFFFFF",
    tabInactiveText: "#b85c7a",
    tabInactiveBg: "#FAF0F4",
    rowHover: "#FFFBFD",
    colHeaderBg: "#FAF0F4",
    colHeaderText: "#b85c7a",
    scoreBg: "#FFF0F5",
    scoreColor: "#e06a8c",
    footerBg: "#FAF0F4",
    footerText: "#a87d90",
  };

  return (
    <div
      className="w-full my-8 rounded-[24px] overflow-hidden bg-white border-2"
      style={{ borderColor: C.border, boxShadow: "0 10px 30px rgba(224,106,140,0.06)" }}
    >
      {/* 🏆 ヘッダー */}
      {title && (
        <div
          className="px-4 md:px-6 py-3.5 font-black text-sm md:text-base flex items-center justify-between"
          style={{ background: C.headerBg, color: C.headerText, borderBottom: `2px solid ${C.border}` }}
        >
          <span className="flex items-center gap-1.5">✨ {title}</span>
        </div>
      )}

      {/* 🔮 タブ切り替えボタン */}
      <div
        className="flex p-1.5 gap-1.5"
        style={{ background: "#FFFBFD", borderBottom: `1.5px solid ${C.border}` }}
      >
        {TABS.map((tab) => {
          const active = activeTab === tab.key;
          return (
            <button
              key={tab.key}
              onClick={() => setActiveTab(tab.key)}
              className="flex-1 py-2 rounded-lg text-[10px] md:text-xs font-black transition-all duration-300 flex items-center justify-center gap-1 active:scale-98 border"
              style={{
                color: active ? C.tabActiveText : C.tabInactiveText,
                background: active ? C.tabActiveBg : C.tabInactiveBg,
                borderColor: active ? C.tabActiveBg : C.border,
                boxShadow: active ? "0 3px 8px rgba(224,106,140,0.2)" : "none",
              }}
            >
              <span>{tab.icon}</span>
              <span>{tab.label}</span>
            </button>
          );
        })}
      </div>

      {/* 📦 商品リスト表示エリア */}
      <div className="divide-y" style={{ borderColor: C.border }}>
        {displayed.map((p, idx) => (
          <div
            key={p.name}
            className="group p-4 md:p-6 bg-white transition-all duration-300 hover:bg-neutral-50/30"
            style={{ contentVisibility: 'auto' }}
          >
            {/* 上部: メイン商品情報レイアウト */}
            <div className="flex flex-col md:flex-row gap-4 md:gap-5 items-start">
              
              {/* 順位 & 画像 */}
              <div className="flex flex-row md:flex-col items-center gap-3 w-full md:w-auto">
                <RankBadge rank={idx + 1} />
                <div className="relative">
                  {p.imageUrl ? (
                    <div
                      className="w-20 h-20 md:w-28 md:h-28 rounded-[16px] md:rounded-[20px] overflow-hidden bg-white flex items-center justify-center border border-pink-100 p-1 group-hover:scale-102 transition-transform duration-300"
                      style={{ boxShadow: '0 6px 20px rgba(224,106,140,0.06)' }}
                    >
                      <img
                        src={p.imageUrl}
                        alt={p.name}
                        className="object-contain w-full h-full"
                        style={{ borderRadius: '12px', mixBlendMode: 'multiply' }}
                        referrerPolicy="no-referrer"
                        loading="lazy"
                        decoding="async"
                      />
                    </div>
                  ) : (
                    <div
                      className="w-20 h-20 md:w-28 md:h-28 rounded-[16px] md:rounded-[20px] overflow-hidden bg-pink-50/50 flex items-center justify-center border border-pink-100"
                    >
                      <span className="text-2xl">🎁</span>
                    </div>
                  )}
                  {/* スコアバッジをモバイル時は画像の上に重ねる */}
                  <div className="absolute bottom-[-6px] right-[-6px] md:bottom-[-10px] md:right-[-10px] bg-white border border-pink-200 shadow-md rounded-full px-2 py-0.5 md:px-2.5 md:py-1 flex flex-col items-center">
                    <span className="text-[10px] md:text-[11px] font-black text-pink-500 leading-none">{p.score.toFixed(2)}</span>
                    <span className="text-[6px] md:text-[7px] font-bold text-gray-400 scale-90 leading-none">SCORE</span>
                  </div>
                </div>
                
                <div className="md:hidden flex-1 pl-2">
                  {p.brand && <p className="text-[9px] font-bold text-muted mb-0.5">{p.brand}</p>}
                  <h3 className="text-xs font-black text-foreground group-hover:text-primary transition-colors leading-snug line-clamp-2">
                    {p.name}
                  </h3>
                </div>
              </div>

              {/* 中央: 商品スペック、特長、メリット・デメリット */}
              <div className="flex-1 w-full">
                {/* ブランド・商品名 (PC向け) */}
                <div className="hidden md:block mb-3">
                  {p.brand && <span className="text-[10px] font-black text-muted/60 uppercase tracking-wider">{p.brand}</span>}
                  <h3 className="text-lg font-black text-foreground group-hover:text-primary transition-colors leading-snug">
                    {p.name}
                  </h3>
                </div>

                {/* 特徴タグ (Features) */}
                {p.features && p.features.length > 0 && (
                  <div className="flex flex-wrap gap-1.5 mb-2.5">
                    {p.features.map(f => (
                      <span
                        key={f}
                        className="text-[9px] md:text-[10px] font-bold px-2 py-0.5 md:px-2.5 md:py-1 rounded-lg border bg-pink-50/30 text-pink-600 border-pink-100 flex items-center gap-1 shadow-sm"
                      >
                        {f}
                      </span>
                    ))}
                  </div>
                )}

                {/* 一言解説 (Description) */}
                {p.description && (
                  <p className="text-[11px] md:text-xs font-bold text-muted/80 leading-relaxed mb-3 pl-2.5 border-l-2 border-pink-200">
                    {p.description}
                  </p>
                )}

                {/* メリット＆デメリット (Pros & Cons) - 最も視覚的価値が高い */}
                {((p.pros && p.pros.length > 0) || (p.cons && p.cons.length > 0)) && (
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-2.5 mt-2 bg-pink-50/10 p-2.5 md:p-3 rounded-2xl border border-pink-50">
                    
                    {/* メリット */}
                    {p.pros && p.pros.length > 0 && (
                      <div className="flex flex-col gap-1">
                        <span className="text-[9px] md:text-[10px] font-black text-emerald-600 flex items-center gap-1 bg-emerald-50 px-1.5 py-0.5 rounded-md w-fit border border-emerald-100">
                          👍 メリット・良い点
                        </span>
                        <ul className="list-none p-0 m-0 flex flex-col gap-1">
                          {p.pros.map((pro, index) => (
                            <li key={index} className="text-[11px] md:text-xs font-bold text-neutral-700 flex items-start gap-1">
                              <span className="text-emerald-500 font-extrabold flex-shrink-0">✓</span>
                              <span>{pro}</span>
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}

                    {/* デメリット */}
                    {p.cons && p.cons.length > 0 && (
                      <div className="flex flex-col gap-1 mt-1 md:mt-0">
                        <span className="text-[9px] md:text-[10px] font-black text-amber-600 flex items-center gap-1 bg-amber-50 px-1.5 py-0.5 rounded-md w-fit border border-amber-100">
                          ⚠️ デメリット・気になる点
                        </span>
                        <ul className="list-none p-0 m-0 flex flex-col gap-1">
                          {p.cons.map((con, index) => (
                            <li key={index} className="text-[11px] md:text-xs font-bold text-neutral-600 flex items-start gap-1">
                              <span className="text-amber-500 font-extrabold flex-shrink-0">⚠</span>
                              <span>{con}</span>
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}

                  </div>
                )}
              </div>

              {/* 右側: 評価スコア & アフィリエイトボタン */}
              <div className="flex flex-col items-center md:items-end justify-center gap-3 w-full md:w-auto md:border-l md:border-pink-50 md:pl-5 md:min-h-[140px]">
                
                {/* 総合評価スコア (PC向け) */}
                <div className="hidden md:flex flex-col items-end gap-1 mb-2">
                  <div className="flex items-baseline gap-1">
                    <span className="text-2xl font-black tracking-tight" style={{ color: C.scoreColor }}>{p.score.toFixed(2)}</span>
                    <span className="text-[9px] font-black text-gray-400">/ 5.0</span>
                  </div>
                  <Stars score={p.score} />
                </div>

                {/* 購入アフィリエイトボタングループ - スマホ横並び3等分 / PC縦積み */}
                <div className="grid grid-cols-3 md:flex md:flex-col gap-1.5 md:gap-2 w-full mt-1.5 md:mt-0">
                  {p.amazon && (
                    <BuyButton
                      label="Amazon"
                      shortLabel="Amazon"
                      price={p.amazon.price}
                      url={p.amazon.url}
                      bg="#FFF8F2"
                      textColor="#FF9900"
                      hoverBg="#FFEEDD"
                      iconUrl="https://www.amazon.co.jp/favicon.ico"
                    />
                  )}
                  {p.rakuten && (
                    <BuyButton
                      label="楽天市場"
                      shortLabel="楽天"
                      price={p.rakuten.price}
                      url={p.rakuten.url}
                      bg="#FFF5F5"
                      textColor="#BF0000"
                      hoverBg="#FFEAE8"
                      iconUrl="https://www.rakuten.co.jp/favicon.ico"
                    />
                  )}
                  {p.yahoo && (
                    <BuyButton
                      label="Yahoo!"
                      shortLabel="Yahoo"
                      price={p.yahoo.price}
                      url={p.yahoo.url}
                      bg="#FFF3F5"
                      textColor="#FF0033"
                      hoverBg="#FFE3E7"
                      iconUrl="https://shopping.yahoo.co.jp/favicon.ico"
                    />
                  )}
                </div>

              </div>

            </div>
          </div>
        ))}
      </div>

      {/* 📎 フッター */}
      <div
        className="px-4 md:px-6 py-2.5 text-[9px] md:text-[10px] font-bold text-center md:text-right"
        style={{ background: C.footerBg, color: C.footerText, borderTop: `2px solid ${C.border}` }}
      >
        ※ 掲載価格およびスペック情報は、各ECモールでの検証時点のものです。最新価格は各ショップページにてご確認ください。
      </div>
    </div>
  );
}

