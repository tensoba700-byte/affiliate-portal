import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

export function middleware(request: NextRequest) {
  const host = request.headers.get('host');
  const { pathname, search } = request.nextUrl;

  // 1. www なしから www ありへの 301 永久リダイレクト (インフラのwwwあり強制と一致させる)
  if (host === 'mikke-style.com') {
    return NextResponse.redirect(
      new URL(pathname + search, 'https://www.mikke-style.com'),
      301
    );
  }

  // 2. 旧「防晒クリーム」記事から新「日焼け止めクリーム」記事への 301 リダイレクト (wwwありで統一)
  const oldSlugEncoded = encodeURIComponent('20260420-新製品レビュー：最新の防晒クリーム');
  const oldSlugDecoded = '20260420-新製品レビュー：最新の防晒クリーム';
  
  if (pathname.includes(oldSlugEncoded) || pathname.includes(encodeURIComponent(oldSlugDecoded)) || pathname.includes('20260420-%E6%96%B0%E8%A3%BD%E5%93%81%E3%83%AC%E3%83%93%E3%83%A5%E3%83%BC%EF%BC%9A%E6%9C%80%E6%96%B0%E3%81%AE%E9%98%B2%E6%99%92%E3%82%AF%E3%83%AA%E3%83%BC%E3%83%A0')) {
    const newSlugEncoded = encodeURIComponent('20260420-新製品レビュー：最新の日焼け止めクリーム');
    return NextResponse.redirect(
      new URL(`/articles/${newSlugEncoded}`, 'https://www.mikke-style.com'),
      301
    );
  }

  return NextResponse.next();
}

export const config = {
  matcher: '/:path*',
};
