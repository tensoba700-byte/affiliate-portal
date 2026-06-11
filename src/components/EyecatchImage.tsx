"use client";

import { useState, useEffect } from 'react';
import { usePathname } from 'next/navigation';

/**
 * EyecatchImage — クライアントコンポーネント
 * /public/eyecatch/[slug].png をフル幅で表示。
 * 画像が存在しない場合は onError で非表示にする。
 * /sample 以下のルートの場合は [slug]-sample.png を優先して読み込む。
 */
export function EyecatchImage({ slug, alt }: { slug: string; alt: string }) {
  const pathname = usePathname();
  const isSample = pathname?.startsWith('/sample');
  
  const samplePath = `/eyecatch/${slug}-sample.png`;
  const prodPath = `/eyecatch/${slug}.png`;
  
  const [imgSrc, setImgSrc] = useState(isSample ? samplePath : prodPath);
  const [hasError, setHasError] = useState(false);

  useEffect(() => {
    setImgSrc(isSample ? samplePath : prodPath);
    setHasError(false);
  }, [slug, isSample, samplePath, prodPath]);

  const handleError = (e: React.SyntheticEvent<HTMLImageElement, Event>) => {
    if (isSample && imgSrc === samplePath) {
      setImgSrc(prodPath);
    } else {
      setHasError(true);
      const container = (e.target as HTMLImageElement).parentElement;
      if (container) container.style.display = 'none';
    }
  };

  if (hasError) return null;

  return (
    <div
      className="w-full s-eyecatch-full-width"
    >
      <img
        src={imgSrc}
        alt={`${alt} アイキャッチ画像`}
        loading="eager"
        className="w-full block"
        onError={handleError}
      />
    </div>
  );
}

