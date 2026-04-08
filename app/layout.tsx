import type { Metadata } from "next";
import { Zen_Maru_Gothic, Noto_Sans_JP, Noto_Serif_JP } from "next/font/google";
import Link from "next/link";
import ThemeSwitcher from "@/src/components/ThemeSwitcher";
import Header from "@/src/components/Header";
import SearchBar from "@/src/components/SearchBar";
import Script from "next/script";
import "./globals.css";

const zenMaru = Zen_Maru_Gothic({
  weight: ['400', '500', '700', '900'],
  variable: "--font-zen-maru",
  subsets: ["latin"],
  display: "swap",
});

const notoSans = Noto_Sans_JP({
  weight: ['400', '500', '700', '900'],
  variable: "--font-noto-sans",
  subsets: ["latin"],
  display: "swap",
});

const notoSerif = Noto_Serif_JP({
  weight: ['400', '500', '700', '900'],
  variable: "--font-noto-serif",
  subsets: ["latin"],
  display: "swap",
});

export const metadata: Metadata = {
  title: "みっけ！ | あなたにぴったりの「好き」が見つかる",
  description: "徹底比較して、あなたにぴったりの商品を見つける。毎日の暮らしをもっと素敵に！",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="ja" className={`${zenMaru.variable} ${notoSans.variable} ${notoSerif.variable} h-full antialiased`} data-theme="peach" data-font="sans">
      <head>
        <Script 
          async 
          src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-5656025362252156" 
          crossOrigin="anonymous" 
          strategy="afterInteractive"
        />
      </head>
      <body className="min-h-full flex flex-col bg-background text-foreground transition-colors duration-500">
        
        {/* Navigation Bar - Cute Glassmorphism */}
        <Header />

        <main className="flex-1 flex flex-col w-full">
          {children}
        </main>

        {/* Footer */}
        <footer className="mt-auto border-t-2 border-primary/10 bg-white/50 pt-16 pb-8">
           <div className="container mx-auto px-6 flex flex-col items-center">
             <Link href="/" className="text-3xl font-black text-primary mb-6">
              みっけ！
            </Link>
            <p className="text-sm font-bold text-muted mb-8 text-center">
              あなたの「好き」がきっと見つかる。<br />
              とっておきのおすすめ情報を毎日お届けします。
            </p>
            <nav className="flex flex-wrap justify-center gap-x-8 gap-y-4 text-xs font-bold text-muted mb-12">
              <Link href="#" className="hover:text-primary transition-colors">運営会社</Link>
              <Link href="#" className="hover:text-primary transition-colors">利用規約</Link>
              <Link href="#" className="hover:text-primary transition-colors">プライバシーポリシー</Link>
              <Link href="#" className="hover:text-primary transition-colors">お問い合わせ</Link>
            </nav>
            <div className="text-[10px] text-muted/60 font-bold tracking-wider">
              &copy; {new Date().getFullYear()} MIKKE! ALL RIGHTS RESERVED.
            </div>
          </div>
        </footer>
        <ThemeSwitcher />
      </body>
    </html>
  );
}
