import type { Metadata } from "next";
import { Zen_Maru_Gothic, Noto_Sans_JP } from "next/font/google";
import Link from "next/link";
import ThemeSwitcher from "@/src/components/ThemeSwitcher";
import Header from "@/src/components/Header";
import SearchBar from "@/src/components/SearchBar";
import CookieConsent from "@/src/components/CookieConsent";
import Script from "next/script";
import "./globals.css";

const zenMaru = Zen_Maru_Gothic({
  weight: ['400', '700'],
  variable: "--font-zen-maru",
  subsets: ["latin"],
  display: "swap",
});

const notoSans = Noto_Sans_JP({
  weight: ['400', '700'],
  variable: "--font-noto-sans",
  subsets: ["latin"],
  display: "swap",
});

export const metadata: Metadata = {
  title: {
    default: "みっけ！ | あなたにぴったりの「好き」が見つかる",
    template: "%s | みっけ！"
  },
  description: "徹底比較して、あなたにぴったりの商品を見つける。毎日の暮らしをもっと素敵に！話題のアイテムから隠れた名品まで徹底レビュー。",
  metadataBase: new URL('https://www.mikke-style.com'),
  openGraph: {
    type: 'website',
    locale: 'ja_JP',
    url: 'https://www.mikke-style.com',
    siteName: 'みっけ！',
    images: [
      {
        url: '/og-image.png', // We should add this later or point to a default
        width: 1200,
        height: 630,
        alt: 'みっけ！',
      },
    ],
  },
  twitter: {
    card: 'summary_large_image',
    title: 'みっけ！ | あなたにぴったりの「好き」が見つかる',
    description: '徹底比較して、あなたにぴったりの商品を見つける。',
  },
  verification: {
    google: "QGldIiSvQoKHBytG-q_y3XXNEfwTTicYY0kuoSPD-iA",
  },
  icons: {
    icon: '/favicon.svg',
    shortcut: '/favicon.svg',
    apple: '/favicon.svg',
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="ja" className={`${zenMaru.variable} ${notoSans.variable} h-full antialiased`} data-theme="peach" data-font="sans">
      <head>
        {/* Google Analytics 4 */}
        <Script
          src="https://www.googletagmanager.com/gtag/js?id=G-6SXHM8M2BJ"
          strategy="afterInteractive"
        />
        <Script id="google-analytics" strategy="afterInteractive">
          {`
            window.dataLayer = window.dataLayer || [];
            function gtag(){dataLayer.push(arguments);}
            gtag('js', new Date());
            gtag('config', 'G-6SXHM8M2BJ');
          `}
        </Script>
        
        <Script 
          async 
          src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-5656025362252156" 
          crossOrigin="anonymous" 
          strategy="afterInteractive"
        />
        
        {/* Affiliate Preview Bypass for non-production environments */}
        <Script id="affiliate-preview-bypass" strategy="afterInteractive">
          {`
            (function() {
              if (typeof window !== 'undefined' && window.location.hostname !== 'www.mikke-style.com') {
                document.addEventListener('click', function(e) {
                  var target = e.target;
                  while (target && target.tagName !== 'A') {
                    target = target.parentElement;
                  }
                  if (target && target.tagName === 'A') {
                    var href = target.getAttribute('href') || '';
                    
                    // 1. ValueCommerce (Yahoo! Shopping)
                    if (href.indexOf('ck.jp.ap.valuecommerce.com') !== -1) {
                      var match = href.match(/[?&]vc_url=([^&]+)/);
                      if (match && match[1]) {
                        var directUrl = decodeURIComponent(match[1]);
                        e.preventDefault();
                        window.open(directUrl, '_blank');
                        return;
                      }
                    }
                    
                    // 2. Rakuten Affiliate
                    if (href.indexOf('hb.afl.rakuten.co.jp') !== -1) {
                      var match = href.match(/[?&]pc=([^&]+)/);
                      if (match && match[1]) {
                        var directUrl = decodeURIComponent(match[1]);
                        e.preventDefault();
                        window.open(directUrl, '_blank');
                        return;
                      }
                    }
                  }
                }, true);
              }
            })();
          `}
        </Script>

        <link rel="icon" type="image/svg+xml" href="/favicon.svg" />
      </head>
      <body className="min-h-full flex flex-col bg-background text-foreground transition-colors duration-500">
        
        {/* Navigation Bar - Cute Glassmorphism */}
        <Header />

        <main className="flex-1 flex flex-col w-full">
          {children}
        </main>

        {/* Footer */}
        <footer className="sample-footer">
          <div className="sample-footer-inner">
            <Link href="/" className="sample-footer-logo">
              mikke!
            </Link>
            <p className="sample-footer-desc">
              コスメオタク美容ライターが、忙しい大人のために送る本音の検証コスメポータル。本当に崩れない・荒れない実力派だけを徹底レビュー。
            </p>
            <nav className="sample-footer-nav">
              <Link href="/">HOME</Link>
              <span>|</span>
              <Link href="/company">ABOUT</Link>
              <span>|</span>
              <Link href="/terms">TERMS</Link>
              <span>|</span>
              <Link href="/privacy">PRIVACY</Link>
              <span>|</span>
              <Link href="/contact">CONTACT</Link>
            </nav>
            <p className="sample-footer-copy">
              &copy; {new Date().getFullYear()} MIKKE! ALL RIGHTS RESERVED.
            </p>
          </div>
        </footer>
        <ThemeSwitcher />
        <CookieConsent />
      </body>
    </html>
  );
}
