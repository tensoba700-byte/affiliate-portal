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
import { useState } from "react";

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

/** ランクバッジ */
function RankBadge({ rank }: { rank: number }) {
  const map: Record<number, { bg: string; border: string; emoji: string }> = {
    1: { bg: "#FFF8E7", border: "#F4C430", emoji: "👑" },
    2: { bg: "#F5F5F5", border: "#B0BEC5", emoji: "🥈" },
    3: { bg: "#FFF3E0", border: "#BCAAA4", emoji: "🥉" },
  };
  const s = map[rank] ?? { bg: "#FDF0F5", border: "#F8BBD0", emoji: "" };

  return (
    <div
      className="flex flex-col items-center justify-center w-9 h-9 rounded-full text-xs font-black flex-shrink-0"
      style={{ background: s.bg, border: `2px solid ${s.border}`, color: "#555" }}
    >
      {s.emoji ? (
        <span className="text-base leading-none">{s.emoji}</span>
      ) : (
        <span className="text-[11px] font-black" style={{ color: "#e06a8c" }}>{rank}位</span>
      )}
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

/** 購入ボタン（ロゴアイコン付き） */
function BuyButton({
  label, price, url, bg, iconUrl,
}: {
  label: string; price: string; url: string; bg: string; iconUrl: string;
}) {
  if (!url && !price) return null;
  return (
    <a
      href={url || "#"}
      target="_blank"
      rel="noopener noreferrer"
      className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-white text-[10px] font-black transition-all hover:opacity-90 hover:-translate-y-0.5 active:scale-95 whitespace-nowrap shadow-sm"
      style={{ background: bg, minWidth: "80px" }}
    >
      {/* ロゴアイコン */}
      <span className="bg-white rounded-full p-0.5 flex-shrink-0 flex items-center justify-center">
        <img
          src={iconUrl}
          alt={label}
          width={16}
          height={16}
          className="object-contain"
          style={{ borderRadius: "2px" }}
        />
      </span>
      {/* テキスト */}
      <span className="flex flex-col leading-tight">
        <span className="opacity-80">{label}</span>
        {price && <span className="text-[11px]">{price}</span>}
      </span>
    </a>
  );
}

type Props = {
  products: Product[];
  title?: string;
};

export default function RankingTable({ products, title }: Props) {
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
        className="hidden md:grid grid-cols-[2.5rem_4rem_1fr_5rem_auto] gap-3 items-center px-5 py-2.5 text-[11px] font-black"
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
          <div
            key={p.name}
            className="grid grid-cols-1 md:grid-cols-[2.5rem_4rem_1fr_5rem_auto] gap-3 items-center px-4 py-4 bg-white transition-colors"
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

            {/* 画像（モバイル・PC共通） */}
            <div className="flex items-center justify-center">
              {p.imageUrl ? (
                <img
                  src={p.imageUrl}
                  alt={p.name}
                  width={64}
                  height={64}
                  className="object-contain rounded-lg w-12 h-12 md:w-16 md:h-16"
                  style={{ border: `1px solid ${C.border}` }}
                />
              ) : (
                <div
                  className="w-12 h-12 md:w-16 md:h-16 rounded-lg flex items-center justify-center text-lg"
                  style={{ background: C.headerBg }}
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

            {/* 画像（PC） */}
            <div className="hidden md:flex items-center justify-center">
              {p.imageUrl ? (
                <img
                  src={p.imageUrl}
                  alt={p.name}
                  width={42}
                  height={42}
                  className="object-contain rounded-lg"
                  style={{ border: `1px solid ${C.border}` }}
                />
              ) : (
                <div
                  className="w-[42px] h-[42px] rounded-lg flex items-center justify-center text-lg"
                  style={{ background: C.headerBg }}
                >
                  🎀
                </div>
              )}
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
                  bg="#F2994A"
                  iconUrl="https://www.amazon.co.jp/favicon.ico"
                />
              )}
              {p.rakuten && (
                <BuyButton
                  label="楽天"
                  price={p.rakuten.price}
                  url={p.rakuten.url}
                  bg="#b85c7a"
                  iconUrl="https://www.rakuten.co.jp/favicon.ico"
                />
              )}
              {p.yahoo && (
                <BuyButton
                  label="ヤフー"
                  price={p.yahoo.price}
                  url={p.yahoo.url}
                  bg="#e06a8c"
                  iconUrl="https://shopping.yahoo.co.jp/favicon.ico"
                />
              )}
            </div>
          </div>
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
