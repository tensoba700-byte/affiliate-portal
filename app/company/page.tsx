import React from 'react';

export const metadata = {
  title: '運営者情報',
  description: 'みっけ！を運営している編集部の情報について記載しています。',
};

export default function CompanyPage() {
  return (
    <div className="container mx-auto max-w-4xl px-4 py-16 animate-fade-in-up">
      <header className="text-center mb-12">
        <div className="inline-block bg-primary/10 text-primary px-4 py-1.5 rounded-full text-xs font-black mb-4">
          Publisher
        </div>
        <h1 className="text-3xl md:text-4xl font-black text-foreground mb-4">
          運営者情報
        </h1>
        <p className="text-sm font-bold text-muted">「みっけ！」を作っている人たち</p>
      </header>

      <div className="bg-white rounded-[2rem] p-8 md:p-12 cute-shadow border border-card-border">
        
        <div className="space-y-0 divide-y divide-primary/10">
          
          <div className="py-6 grid grid-cols-1 md:grid-cols-3 items-center">
            <span className="text-sm font-black text-muted mb-2 md:mb-0">サイト名</span>
            <span className="md:col-span-2 text-base font-bold text-foreground">みっけ！</span>
          </div>

          <div className="py-6 grid grid-cols-1 md:grid-cols-3 items-center">
            <span className="text-sm font-black text-muted mb-2 md:mb-0">URL</span>
            <span className="md:col-span-2 text-base font-bold text-primary">
              <a href="https://www.mikke-style.com" target="_blank" rel="noopener noreferrer">https://www.mikke-style.com</a>
            </span>
          </div>

          <div className="py-6 grid grid-cols-1 md:grid-cols-3 items-center">
            <span className="text-sm font-black text-muted mb-2 md:mb-0">運営者</span>
            <span className="md:col-span-2 text-base font-bold text-foreground">みっけ！編集部（田中 太郎）</span>
          </div>

          <div className="py-6 grid grid-cols-1 md:grid-cols-3 items-center">
            <span className="text-sm font-black text-muted mb-2 md:mb-0">お問い合わせ</span>
            <span className="md:col-span-2 text-base font-bold text-foreground">contact@mikke-style.com</span>
          </div>

          <div className="py-6 grid grid-cols-1 md:grid-cols-3 items-start">
            <span className="text-sm font-black text-muted mb-2 md:mb-0">事業内容</span>
            <div className="md:col-span-2 text-sm font-bold text-foreground/80 leading-relaxed">
              <p>1. 日用品、家電、ガジェット等の比較・レビューメディアの運営</p>
              <p>2. アフィリエイト広告事業</p>
              <p>3. コンテンツ企画・制作</p>
            </div>
          </div>

        </div>

        <div className="mt-12 bg-primary/5 rounded-3xl p-6 md:p-8 text-center">
          <h3 className="text-lg font-black text-primary mb-4">MIKKE! のミッション</h3>
          <p className="text-sm font-bold text-foreground/80 leading-relaxed italic">
            「探していた『好き』に、もっとワクワクを。」<br />
            私たちは、溢れる情報の中からあなたにぴったりの「正解」を見つけ出すお手伝いをしています。<br />
            日々の暮らしが少しだけ、でも確実に豊かになるような情報を発信し続けます。
          </p>
        </div>

      </div>
    </div>
  );
}
