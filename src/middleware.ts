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

  let decodedPathname = '';
  try {
    decodedPathname = decodeURIComponent(pathname);
  } catch (e) {
    // Safe fallback if URI is malformed
  }

  const normalizedDecodedPath = decodedPathname.normalize('NFC');

  // 2. 旧「防晒クリーム」記事から新「日焼け止めクリーム」記事への 301 リダイレクト
  const oldSunscreenSlug = '20260420-新製品レビュー：最新の防晒クリーム'.normalize('NFC');
  if (normalizedDecodedPath.includes(oldSunscreenSlug)) {
    const newSlugEncoded = encodeURIComponent('20260420-新製品レビュー：最新の日焼け止めクリーム');
    return NextResponse.redirect(
      new URL(`/articles/${newSlugEncoded}`, 'https://www.mikke-style.com'),
      301
    );
  }

  // 3. 旧日本語スマートウォッチ記事から新英数字スラッグ記事への 301 リダイレクト
  const oldWatchSlug = '20260525-腕に未来の健康を灯す2026年最新スマートウォッチ徹底比較'.normalize('NFC');
  if (normalizedDecodedPath.includes(oldWatchSlug)) {
    return NextResponse.redirect(
      new URL('/articles/20260525-smartwatch-comparison', 'https://www.mikke-style.com'),
      301
    );
  }

  // 4. 過去に削除された古い記事URLから記事一覧への 301 リダイレクト (404エラー防止)
  const deletedSlugs = [
    '20260524-日常に小さな贅沢を重ねる収納上手なスタッキングマグ6選',
    '20260411-telework-gadgets-f401',
    '20240411-telework-gadgets-453f',
    '20240411-telework-gadgets-fdb2',
    '20260409-究極のガジェット-選りすぐり',
    '20260410-最新デスクガジェット-生産性向上',
    '20260408-インテリア-0dda',
    '20260408-ガジェット-9465',
    '20260408-便利グッズ-b199',
    '20260408-生活雑貨-00ac',
    '20260408-美容スキンケア-a85f',
    '20260409-ガジェット-神アイテム'
  ].map(s => s.normalize('NFC'));

  for (const slug of deletedSlugs) {
    if (normalizedDecodedPath.includes(slug)) {
      return NextResponse.redirect(
        new URL('/articles', 'https://www.mikke-style.com'),
        301
      );
    }
  }

  return NextResponse.next();
}

export const config = {
  matcher: '/:path*',
};
