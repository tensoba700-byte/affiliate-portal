import React from 'react';

export const metadata = {
  title: '利用規約',
  description: 'みっけ！の利用規約について記載しています。',
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
            <span className="text-primary">📜</span> はじめに
          </h2>
          <p>
            本利用規約（以下「本規約」）は、「みっけ！」（以下「当サイト」）が提供するサービス（以下「本サービス」）の利用条件を定めるものです。ユーザーの皆様には、本規約に従って本サービスをご利用いただきます。
          </p>
        </section>

        <section>
          <h2 className="text-xl font-black text-foreground mb-4 flex items-center gap-2">
            <span className="text-primary">⚖️</span> 免責事項
          </h2>
          <ul className="list-disc list-inside space-y-2">
            <li>当サイトに掲載されている情報については、可能な限り正確な情報を掲載するよう努めておりますが、その正確性や信頼性を保証するものではありません。</li>
            <li>当サイトの情報を利用したことで生じたトラブルや、損失・損害等について、理由の如何を問わず、当サイトは一切の責任を負いかねます。</li>
            <li>当サイトからリンクされた外部サイトの内容についても、一切の責任を負いません。</li>
            <li>商品の購入やサービスの利用は、ユーザーご自身の判断と責任において行ってください。</li>
          </ul>
        </section>

        <section>
          <h2 className="text-xl font-black text-foreground mb-4 flex items-center gap-2">
            <span className="text-primary">🎨</span> 著作権について
          </h2>
          <p>
            当サイトに掲載されている全てのコンテンツ（ロゴ、文章、画像、動画、デザイン、表現等）の著作権は、当サイトまたは各権利者に帰属します。これらの情報の無断転載、複製、販売等の二次利用は固く禁じます。引用を行う際は、当サイトの名称およびリンクを明記する等の著作権法上認められた範囲内で行ってください。
          </p>
        </section>

        <section>
          <h2 className="text-xl font-black text-foreground mb-4 flex items-center gap-2">
            <span className="text-primary">🔗</span> リンクについて
          </h2>
          <p>
            当サイトは原則としてリンクフリーです。リンクを行う場合の許可や連絡は不要ですが、インラインフレーム等の使用により、当サイトのコンテンツであることが不明確になるような方法でのリンクはお断りします。
          </p>
        </section>

        <section>
          <h2 className="text-xl font-black text-foreground mb-4 flex items-center gap-2">
            <span className="text-primary">🔄</span> 利用規約の変更
          </h2>
          <p>
            当サイトは、必要と判断した場合には、ユーザーに通知することなくいつでも本規約を変更することができるものとします。なお、本規約の変更後、本サービスの利用を開始した場合には、当該ユーザーは変更後の規約に同意したものとみなします。
          </p>
        </section>

        <div className="pt-8 border-t border-primary/10 text-right">
          <p className="text-xs font-bold text-muted">最終更新日：2026年4月16日</p>
          <p className="text-xs font-bold text-muted">みっけ！編集部</p>
        </div>
      </div>
    </div>
  );
}
