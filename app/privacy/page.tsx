import React from 'react';

export const metadata = {
  title: 'プライバシーポリシー',
  description: 'みっけ!のプライバシーポリシー（個人情報保護方針）について記載しています。',
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
            <span className="text-primary">👤</span> 1. 個人情報の取得について
          </h2>
          <p className="text-sm md:text-base leading-relaxed text-foreground/80">
            当サイトでは、お問い合わせフォームをご利用の際に、お名前・メールアドレス等の個人情報をご提供いただく場合があります。取得した個人情報は、お問い合わせへの回答のみに使用し、第三者への提供は行いません。
          </p>
        </section>

        <section>
          <h2 className="text-xl font-black text-foreground mb-4 flex items-center gap-2">
            <span className="text-primary">📊</span> 2. アクセス解析ツールについて
          </h2>
          <p className="text-sm md:text-base leading-relaxed text-foreground/80">
            当サイトでは、Googleが提供するアクセス解析ツール「Google Analytics 4」を使用しています。Google Analytics 4はトラフィックデータの収集のためにCookieを使用しています。このトラフィックデータは匿名で収集されており、個人を特定するものではありません。この機能はCookieを無効にすることで収集を拒否できます。詳しくはGoogleのプライバシーポリシーをご覧ください。
          </p>
        </section>

        <section>
          <h2 className="text-xl font-black text-foreground mb-4 flex items-center gap-2">
            <span className="text-primary">📢</span> 3. 広告の配信について
          </h2>
          <div className="space-y-6 text-sm md:text-base leading-relaxed text-foreground/80">
            <div>
              <h3 className="font-black text-foreground mb-2">Googleアドセンスについて</h3>
              <p>
                当サイトはGoogleが提供する広告配信サービス「Google AdSense」を利用しています。Google AdSenseは、ユーザーの興味に応じた広告を表示するためにCookieを使用しています。Cookieを使用することで、当サイトや他のサイトへのアクセス情報に基づいて、ユーザーに適切な広告が表示されます。Cookieを無効にする方法やGoogleアドセンスに関する詳細は、Googleのポリシーと規約ページをご覧ください。
              </p>
            </div>
            <div>
              <h3 className="font-black text-foreground mb-2">アフィリエイト広告について</h3>
              <p>
                当サイトは以下のアフィリエイトプログラムに参加しています。記事内のリンクから商品を購入された場合、当サイトに一定の報酬が発生することがあります。ただし、読者の方に追加の費用が発生することは一切ありません。
              </p>
              <ul className="list-disc list-inside mt-2 space-y-1">
                <li>Amazonアソシエイト・プログラム（Amazon Associates）</li>
                <li>楽天アフィリエイト</li>
                <li>Google AdSense</li>
                <li>A8.net</li>
              </ul>
              <p className="mt-2 text-xs font-bold text-muted italic">
                紹介している商品・サービスはすべて編集部が独自に選定しており、報酬の有無が評価内容に影響することはありません。
              </p>
            </div>
          </div>
        </section>

        <section>
          <h2 className="text-xl font-black text-foreground mb-4 flex items-center gap-2">
            <span className="text-primary">🍪</span> 4. Cookieについて
          </h2>
          <p className="text-sm md:text-base leading-relaxed text-foreground/80">
            当サイトでは、利便性の向上やアクセス解析のためにCookieを使用しています。ブラウザの設定によりCookieを無効にすることができますが、一部のサービスが正常に動作しない場合があります。
          </p>
        </section>

        <section>
          <h2 className="text-xl font-black text-foreground mb-4 flex items-center gap-2">
            <span className="text-primary">⚠️</span> 5. 免責事項
          </h2>
          <p className="text-sm md:text-base leading-relaxed text-foreground/80">
            当サイトのコンテンツ・情報については、できる限り正確な情報を提供するよう努めておりますが、正確性・安全性を保証するものではありません。当サイトに掲載された内容によって生じた損害等の一切の責任を負いかねますのでご了承ください。また、当サイトからリンクやバナーなどによって他のサイトに移動された場合、移動先サイトで提供される情報・サービス等について一切の責任を負いません。
          </p>
        </section>

        <section>
          <h2 className="text-xl font-black text-foreground mb-4 flex items-center gap-2">
            <span className="text-primary">🔄</span> 6. プライバシーポリシーの変更について
          </h2>
          <p className="text-sm md:text-base leading-relaxed text-foreground/80">
            当サイトは、個人情報に関して適用される日本の法令を遵守するとともに、本プライバシーポリシーの内容を適宜見直し、改善してまいります。修正された最新のプライバシーポリシーは常に本ページにて開示いたします。
          </p>
        </section>

        <div className="pt-8 border-t border-primary/10 text-right">
          <p className="text-xs font-bold text-muted">最終更新日：2026年4月18日</p>
          <p className="text-xs font-bold text-muted">みっけ!編集部</p>
        </div>
      </div>
    </div>
  );
}
