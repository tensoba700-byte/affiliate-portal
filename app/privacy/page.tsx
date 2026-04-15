import React from 'react';

export const metadata = {
  title: 'プライバシーポリシー',
  description: 'みっけ！のプライバシーポリシー（個人情報保護方針）について記載しています。',
};

export default function PrivacyPage() {
  return (
    <div className="container mx-auto max-w-4xl px-4 py-16 animate-fade-in-up">
      <header className="text-center mb-12">
        <div className="inline-block bg-primary/10 text-primary px-4 py-1.5 rounded-full text-xs font-black mb-4">
          Legal
        </div>
        <h1 className="text-3xl md:text-4xl font-black text-foreground mb-4">
          プライバシーポリシー
        </h1>
        <p className="text-sm font-bold text-muted">個人情報の取り扱いと広告配信について</p>
      </header>

      <div className="bg-white rounded-[2rem] p-8 md:p-12 cute-shadow border border-card-border space-y-10">
        
        <section>
          <h2 className="text-xl font-black text-foreground mb-4 flex items-center gap-2">
            <span className="text-primary">📌</span> 個人情報の保護について
          </h2>
          <p className="text-sm md:text-base leading-relaxed text-foreground/80">
            「みっけ！」（以下、当サイト）では、お問い合わせやコメントの際、お名前、メールアドレス等の個人情報をご登録いただく場合がございます。これらの個人情報は質問に対する回答や必要な情報を電子メールなどをでご連絡する場合に利用させていただくものであり、個人情報をご提供いただく際の目的以外では利用いたしません。
          </p>
        </section>

        <section>
          <h2 className="text-xl font-black text-foreground mb-4 flex items-center gap-2">
            <span className="text-primary">📢</span> 広告の配信について
          </h2>
          <div className="space-y-4 text-sm md:text-base leading-relaxed text-foreground/80">
            <p>
              当サイトでは、第三者配信の広告サービス「Googleアドセンス」を利用しています。広告配信事業者は、ユーザーの興味に応じた商品やサービスの広告を表示するため、当サイトや他サイトへのアクセスに関する情報 「Cookie」(氏名、住所、メール アドレス、電話番号は含まれません) を使用することがあります。
            </p>
            <p>
              Googleアドセンスに関して、このプロセスの詳細やこのような情報が広告配信事業者に使用されないようにする方法については、
              <a href="https://policies.google.com/technologies/ads" target="_blank" rel="noopener noreferrer" className="text-primary underline underline-offset-4 decoration-2">Googleのポリシーと規約</a> 
              をご覧ください。
            </p>
          </div>
        </section>

        <section>
          <h2 className="text-xl font-black text-foreground mb-4 flex items-center gap-2">
            <span className="text-primary">📦</span> アフィリエイトプログラムについて
          </h2>
          <p className="text-sm md:text-base leading-relaxed text-foreground/80">
            当サイトは、Amazon.co.jpを宣伝しリンクすることによってサイトが紹介料を獲得できる手段を提供することを目的に設定されたアフィリエイトプログラムである、Amazonアソシエイト・プログラムの参加者です。
            また、楽天市場、Yahoo!ショッピング等のアフィリエイトプログラムも利用しています。第三者がコンテンツおよび宣伝を提供し、訪問者から直接情報を収集し、訪問者のブラウザにCookieを設定したりこれを認識したりする場合があります。
          </p>
        </section>

        <section>
          <h2 className="text-xl font-black text-foreground mb-4 flex items-center gap-2">
            <span className="text-primary">📊</span> アクセス解析ツールについて
          </h2>
          <p className="text-sm md:text-base leading-relaxed text-foreground/80">
            当サイトでは、Googleによるアクセス解析ツール「Googleアナリティクス」を利用しています。このGoogleアナリティクスはトラフィックデータの収集のためにCookieを使用しています。このトラフィックデータは匿名で収集されており、個人を特定するものではありません。この機能はCookieを無効にすることで収集を拒否することが出来ますので、お使いのブラウザの設定をご確認ください。
          </p>
        </section>

        <section>
          <h2 className="text-xl font-black text-foreground mb-4 flex items-center gap-2">
            <span className="text-primary">⚠️</span> 免責事項
          </h2>
          <p className="text-sm md:text-base leading-relaxed text-foreground/80">
            当サイトからリンクやバナーなどによって他のサイトに移動された場合、移動先サイトで提供される情報、サービス等について一切の責任を負いません。当サイトのコンテンツ・情報につきまして、可能な限り正確な情報を掲載するよう努めておりますが、誤情報が入り込んだり、情報が古くなっていることもございます。当サイトに掲載された内容によって生じた損害等の一切の責任を負いかねますのでご了承ください。
          </p>
        </section>

        <div className="pt-8 border-t border-primary/10 text-right">
          <p className="text-xs font-bold text-muted">策定日：2026年4月16日</p>
          <p className="text-xs font-bold text-muted">みっけ！編集部</p>
        </div>
      </div>
    </div>
  );
}
