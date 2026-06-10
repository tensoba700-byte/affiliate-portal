import Link from 'next/link';

export default function NotFound() {
  return (
    <div className="flex flex-col items-center justify-center min-h-[70vh] px-6 text-center animate-fade-in-up">
      <div className="relative mb-8">
        <span className="text-9xl opacity-10 font-black absolute inset-0 flex items-center justify-center -z-10 select-none">404</span>
        <span className="text-[120px] block">🔍</span>
      </div>
      
      <h1 className="text-3xl md:text-4xl font-black text-foreground mb-4">
        ページがみつかりませんでした
      </h1>
      
      <p className="text-muted font-bold mb-10 max-w-md mx-auto leading-relaxed">
        お探しのページは移動したか、削除された可能性があります。<br />
        トップページから気になるアイテムをみつけてね！
      </p>
      
      <div className="flex flex-col sm:flex-row gap-4 items-center">
        <Link 
          href="/" 
          className="px-10 py-4 rounded-[4px] bg-primary text-white font-black text-sm hover:bg-primary/90 transition-all duration-300 shadow-lg hover:cute-shadow hover:-translate-y-1"
        >
          ホームへもどる 🍓
        </Link>
        <Link 
          href="/articles" 
          className="px-10 py-4 rounded-[4px] bg-white border-2 border-primary/10 text-primary font-black text-sm hover:border-primary transition-all duration-300"
        >
          記事一覧を見る
        </Link>
      </div>
      
      {/* Decorative blobs */}
      <div className="fixed top-1/4 -left-20 w-64 h-64 bg-primary/5 rounded-full blur-3xl -z-10 pointer-events-none"></div>
      <div className="fixed bottom-1/4 -right-20 w-64 h-64 bg-yellow-300/5 rounded-full blur-3xl -z-10 pointer-events-none"></div>
    </div>
  );
}
