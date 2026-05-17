"use client";

/**
 * EyecatchImage — クライアントコンポーネント
 * /public/eyecatch/[slug].png をフル幅で表示。
 * 画像が存在しない場合は onError で非表示にする。
 */
export function EyecatchImage({ slug, alt }: { slug: string; alt: string }) {
  return (
    <div
      style={{ borderRadius: '16px', overflow: 'hidden', marginBottom: '24px', aspectRatio: '16 / 9', width: '100%' }}
      className="w-full"
    >
      <img
        src={`/eyecatch/${slug}.png`}
        alt={`${alt} アイキャッチ画像`}
        loading="eager"
        style={{ aspectRatio: '16 / 9', objectFit: 'cover', width: '100%', height: '100%' }}
        className="w-full block"
        onError={(e) => {
          const container = (e.target as HTMLImageElement).parentElement;
          if (container) container.style.display = 'none';
        }}
      />
    </div>
  );
}
