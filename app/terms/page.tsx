import React from 'react';

export const metadata = {
  title: '利用規約',
  description: 'みっけ！の利用規約について記載しています。',
  alternates: {
    canonical: '/terms',
  },
};

export default function TermsPage() {
  return (
    <div className="container mx-auto max-w-4xl px-4 py-16 animate-fade-in-up">
      <header className="text-center mb-12">
        <div className="inline-block bg-primary/10 text-primary px-4 py-1.5 rounded-full text-xs font-black mb-4">
          Legal
        </div>
        <h1 className="text-3xl md:text-4xl font-black text-foreground mb-4">
          利用規約
        </h1>
        <p className="text-sm font-bold text-muted">本サイトをご利用いただく上でのルール</p>
      </header>

      <div className="bg-white rounded-[2rem] p-8 md:p-12 cute-shadow border border-card-border space-y-10 text-sm md:text-base leading-relaxed text-foreground/80">
        
        <section>
          <h2 className="text-xl font-black text-foreground mb-4 flex items-center gap-2">
            <span className="text-primary">📜</span> 1. はじめに
          </h2>
          <p>
            本利用規約（以下「本規約」）は、みっけ！（以下「当サイト」）が提供するサービスの利用条件を定めるものです。当サイトをご利用の際は、本規約をお読みいただき、同意の上でご利用ください。
          </p>
        </section>

        <section>
          <h2 className="text-xl font-black text-foreground mb-4 flex items-center gap-2">
            <span className="text-primary">⚖️</span> 2. 著作権について
          </h2>
          <p>
            当サイトに掲載されているコンテンツ（文章・画像・イラスト等）の著作権は、当サイト運営者または正当な権利を有する third party に帰属します。無断での転載・複製・改変・再配布等は禁止します。引用する場合は、出典を明記した上で適切な範囲内でご利用ください。
          </p>
        </section>

        <section>
          <h2 className="text-xl font-black text-foreground mb-4 flex items-center gap-2">
            <span className="text-primary">🔗</span> 3. リンクについて
          </h2>
          <div className="space-y-4">
            <p>当サイトへのリンクは原則として自由です。ただし、以下の場合はリンクをお断りします。 </p>
            <ul className="list-disc list-inside space-y-1">
              <li>違法または公序良俗に反するサイト</li>
              <li>当サイトの内容を誹謗・中傷するサイト</li>
              <li>フレーム内に当サイトを表示するサイト</li>
            </ul>
          </div>
        </section>

        <section>
          <h2 className="text-xl font-black text-foreground mb-4 flex items-center gap-2">
            <span className="text-primary">⚠️</span> 4. 免責事項
          </h2>
          <div className="space-y-4">
            <p>
              当サイトに掲載する情報は、可能な限り正確かつ最新の情報を掲載するよう努めておりますが、その内容の正確性・完全性・有用性を保証するものではありません。当サイトの情報を参考にした結果生じた いかなる損害についても、当サイト運営者は一切の責任を負いません。
            </p>
            <p>
              商品の価格・仕様・在庫状況は予告なく変更される場合があります。最新情報は各販売店の公式ページにてご確認ください。
            </p>
          </div>
        </section>

        <section>
          <h2 className="text-xl font-black text-foreground mb-4 flex items-center gap-2">
            <span className="text-primary">📢</span> 5. 広告・アフィリエイトについて
          </h2>
          <p>
            当サイトはアフィリエイトプログラムに参加しており、記事内にアフィリエイトリンクが含まれる場合があります。リンクを経由して商品を購入いただいた場合、当サイトに報酬が発生することがありますが、読者の方への追加費用は一切発生しません。掲載商品の選定・評価は報酬の有無に関わらず独自の基準に基づいて行っています。
          </p>
        </section>

        <section>
          <h2 className="text-xl font-black text-foreground mb-4 flex items-center gap-2">
            <span className="text-primary">🚫</span> 6. 禁止事項
          </h2>
          <div className="space-y-4">
            <p>当サイトの利用にあたり、以下の行為を禁止します。</p>
            <ul className="list-disc list-inside space-y-1">
              <li>当サイトのコンテンツの無断転載・複製</li>
              <li>当サイトへの不正アクセス・サーバーへの過度な負荷をかける行為</li>
              <li>他のユーザーや第三者を誹謗・中傷する行為</li>
              <li>法令または公序良俗に反する行為</li>
              <li>その他、当サイト運営者が不適切と判断する行為</li>
            </ul>
          </div>
        </section>

        <section>
          <h2 className="text-xl font-black text-foreground mb-4 flex items-center gap-2">
            <span className="text-primary">🔄</span> 7. 規約の変更
          </h2>
          <p>
            当サイトは、必要に応じて本規約を変更することがあります。変更後の規約は当ページに掲載した時点から効力を生じるものとします。
          </p>
        </section>

        <section>
          <h2 className="text-xl font-black text-foreground mb-4 flex items-center gap-2">
            <span className="text-primary">⚖️</span> 8. 準拠法・管轄裁判所
          </h2>
          <p>
            本規約の解釈にあたっては、日本法を準拠法とします。当サイトに関して紛争が生じた場合には、当サイト運営者の所在地を管轄する裁判所を専属的合意管轄とします。
          </p>
        </section>

        <div className="pt-8 border-t border-primary/10 text-right">
          <p className="text-xs font-bold text-muted">最終更新日：2026年4月18日</p>
          <p className="text-xs font-bold text-muted">みっけ！編集部</p>
        </div>
      </div>
    </div>
  );
}
