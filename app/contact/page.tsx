import React from 'react';

export const metadata = {
  title: 'お問い合わせ',
  description: 'みっけ！へのお問い合わせはこちらから。記事へのご意見、ご感想、お仕事の依頼などお待ちしております。',
};

export default function ContactPage() {
  return (
    <div className="container mx-auto max-w-4xl px-4 py-16 animate-fade-in-up">
      <header className="text-center mb-12">
        <div className="inline-block bg-primary/10 text-primary px-4 py-1.5 rounded-full text-xs font-black mb-4">
          Contact
        </div>
        <h1 className="text-3xl md:text-4xl font-black text-foreground mb-4">
          お問い合わせ
        </h1>
        <p className="text-sm font-bold text-muted">ご意見・ご感想・お仕事の依頼はこちらから</p>
      </header>

      <div className="bg-white rounded-[2rem] p-8 md:p-12 cute-shadow border border-card-border">
        
        <form className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label htmlFor="name" className="block text-xs font-black text-foreground mb-2 ml-4">
                お名前 (必須)
              </label>
              <input
                type="text"
                id="name"
                name="name"
                required
                placeholder="田中 太郎"
                className="w-full bg-primary/5 border-2 border-transparent focus:border-primary/20 focus:bg-white outline-none rounded-full px-6 py-3 text-sm font-bold transition-all"
              />
            </div>
            <div>
              <label htmlFor="email" className="block text-xs font-black text-foreground mb-2 ml-4">
                メールアドレス (必須)
              </label>
              <input
                type="email"
                id="email"
                name="email"
                required
                placeholder="example@mail.com"
                className="w-full bg-primary/5 border-2 border-transparent focus:border-primary/20 focus:bg-white outline-none rounded-full px-6 py-3 text-sm font-bold transition-all"
              />
            </div>
          </div>

          <div>
            <label htmlFor="subject" className="block text-xs font-black text-foreground mb-2 ml-4">
              件名
            </label>
            <input
              type="text"
              id="subject"
              name="subject"
              placeholder="お仕事のご相談 など"
              className="w-full bg-primary/5 border-2 border-transparent focus:border-primary/20 focus:bg-white outline-none rounded-full px-6 py-3 text-sm font-bold transition-all"
            />
          </div>

          <div>
            <label htmlFor="message" className="block text-xs font-black text-foreground mb-2 ml-4">
              お問い合わせ内容 (必須)
            </label>
            <textarea
              id="message"
              name="message"
              required
              rows={6}
              placeholder="こちらに内容を入力してください..."
              className="w-full bg-primary/5 border-2 border-transparent focus:border-primary/20 focus:bg-white outline-none rounded-3xl px-6 py-4 text-sm font-bold transition-all resize-none"
            ></textarea>
          </div>

          <div className="pt-4">
            <button
              type="submit"
              className="w-full md:w-auto md:px-12 bg-primary text-white text-sm font-black py-4 rounded-full shadow-lg shadow-primary/20 hover:scale-105 active:scale-95 transition-all"
            >
              送信内容を確認する
            </button>
          </div>
        </form>

        <div className="mt-12 pt-8 border-t border-primary/10">
          <h3 className="text-sm font-black text-foreground mb-4">お問い合わせに関する注意事項</h3>
          <ul className="space-y-2 text-[11px] font-bold text-muted leading-relaxed">
            <li>・お送りいただいた内容は編集部で確認し、必要に応じて返信させていただきます。</li>
            <li>・全てのお問い合わせに必ずしも返信をお約束するものではございませんので、予めご了承ください。</li>
            <li>・ご入力いただいた個人情報は、お問い合わせへの回答目的以外には使用いたしません。</li>
          </ul>
        </div>

      </div>
    </div>
  );
}
