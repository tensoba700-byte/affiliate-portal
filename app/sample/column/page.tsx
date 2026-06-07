import Link from 'next/link';

export const columnsData = [
  {
    slug: 'night-pore-reset',
    title: '仕事帰りの10分でできる！夕方の毛穴に絶望しないための夜のリセット習慣',
    excerpt: '日中は忙しすぎてメイク直しをする暇なんて1秒もない！そんな大忙しな大人のために、お風呂前にサッとできる、その日の汚れを完全に溜め込まない極上スキンケアメソッド。',
    date: '2026.06.09',
    category: 'ESSAY & TIPS',
    coverImage: 'https://images.unsplash.com/photo-1556228720-195a672e8a03?w=600&q=80'
  },
  {
    slug: 'honest-makeup-base',
    title: 'コスメオタク美容ライターの本音。本当に「夕方ににじまない」メイク下地の選び方',
    excerpt: '「キープ力抜群！」と謳う下地はたくさんあるけれど、本当に夕方までテカらず、ヨレない本命下地を見分けるための成分とテクスチャーのチェックリスト。',
    date: '2026.06.08',
    category: 'BEAUTY CHECKLIST',
    coverImage: 'https://images.unsplash.com/photo-1608248597279-f99d160bfcbc?w=600&q=80'
  },
  {
    slug: 'morning-three-minute-glow',
    title: '忙しい朝の3分間で透明感を引き出す、プチプラを賢く使った時短保湿術',
    excerpt: '1分1秒が惜しい朝のバタバタタイムに、プチプラシートマスクと乳液の組み合わせだけで、夕方まで乾燥知らずのもちもち肌を作るオタクの裏ワザを大公開！',
    date: '2026.06.05',
    category: 'MORNING ROUTINE',
    coverImage: 'https://images.unsplash.com/photo-1598440947619-2c35fc9aa908?w=600&q=80'
  }
];

export default function SampleColumnList() {
  return (
    <div className="w-full pb-32 pt-12 px-4 bg-background text-foreground min-h-screen relative overflow-x-hidden">
      {/* Force clean-science theme dynamically */}
      <script dangerouslySetInnerHTML={{
        __html: `
          document.documentElement.setAttribute('data-theme', 'clean-science');
          document.documentElement.setAttribute('data-font', 'sans');
        `
      }} />

      {/* Top ambient glow */}
      <div className="absolute top-0 left-1/2 -translate-x-1/2 w-full max-w-7xl h-[400px] bg-gradient-to-b from-zinc-200/30 to-transparent pointer-events-none blur-3xl z-0" />

      <div className="container mx-auto max-w-4xl relative z-10">
        
        {/* Header Breadcrumbs & Title */}
        <div className="mb-16 text-center">
          <nav className="text-[10px] font-bold mb-6 flex items-center justify-center gap-2 text-muted tracking-widest uppercase">
            <Link href="/sample" className="hover:text-primary transition-colors">HOME</Link>
            <span className="text-zinc-400">/</span>
            <span className="text-foreground">BEAUTY JOURNAL</span>
          </nav>
          
          <h1 className="text-3xl md:text-5xl font-black tracking-[0.2em] text-foreground mb-6 font-mono select-none">
            BEAUTY JOURNAL
          </h1>
          <p className="text-xs text-muted font-bold tracking-widest max-w-lg mx-auto leading-relaxed uppercase">
            ESSAYS, TIPS & EXPERIENCES BY BEAUTY GEEKS
          </p>
          <div className="w-12 h-0.5 bg-zinc-950 mx-auto mt-6" />
        </div>

        {/* Featured Column (First Post) */}
        {columnsData.length > 0 && (
          <section className="mb-16">
            <Link 
              href={`/sample/column/${columnsData[0].slug}`}
              className="group flex flex-col md:flex-row gap-8 bg-white border border-card-border rounded-2xl p-6 shadow-sm hover:shadow-md transition-all duration-500"
            >
              <div 
                className="w-full md:w-[450px] aspect-video md:aspect-[4/3] bg-cover bg-center rounded-xl flex-shrink-0 transition-transform duration-500 group-hover:scale-[1.01]"
                style={{ backgroundImage: `url(${columnsData[0].coverImage})` }}
              />
              <div className="flex flex-col justify-between py-2 gap-4">
                <div className="space-y-3">
                  <div className="flex items-center gap-3 text-[9px] font-black text-muted tracking-widest uppercase">
                    <span className="bg-zinc-950 text-white px-2 py-0.5 rounded">{columnsData[0].category}</span>
                    <span>{columnsData[0].date}</span>
                  </div>
                  <h2 className="text-lg md:text-2xl font-black text-foreground leading-snug group-hover:text-zinc-700 transition-colors">
                    {columnsData[0].title}
                  </h2>
                  <p className="text-muted text-xs md:text-sm leading-relaxed font-bold">
                    {columnsData[0].excerpt}
                  </p>
                </div>
                <div className="text-[10px] font-black tracking-widest text-primary flex items-center gap-1 group-hover:translate-x-1 transition-transform pt-4 md:pt-0">
                  READ THE ESSAY <span className="text-xs">→</span>
                </div>
              </div>
            </Link>
          </section>
        )}

        {/* Column Grid (Remaining Posts) */}
        <section className="grid grid-cols-1 md:grid-cols-2 gap-8">
          {columnsData.slice(1).map((col) => (
            <Link
              href={`/sample/column/${col.slug}`}
              key={col.slug}
              className="group flex flex-col bg-white border border-card-border rounded-2xl overflow-hidden hover:shadow-md shadow-sm transition-all duration-500 p-5"
            >
              <div 
                className="w-full aspect-[16/10] bg-cover bg-center rounded-xl transition-transform duration-500 group-hover:scale-[1.01] mb-5"
                style={{ backgroundImage: `url(${col.coverImage})` }}
              />
              
              <div className="flex flex-col flex-1 justify-between gap-3">
                <div className="space-y-2.5">
                  <div className="flex justify-between items-center text-[9px] font-black text-muted tracking-widest uppercase">
                    <span className="bg-zinc-100 text-zinc-800 px-2.5 py-0.5 rounded-full">{col.category}</span>
                    <span>{col.date}</span>
                  </div>
                  <h3 className="text-base font-black text-foreground leading-snug group-hover:text-zinc-700 transition-colors line-clamp-2">
                    {col.title}
                  </h3>
                  <p className="text-muted text-xs leading-relaxed font-bold line-clamp-2">
                    {col.excerpt}
                  </p>
                </div>
                <div className="text-[10px] font-black tracking-widest text-primary flex items-center gap-1 group-hover:translate-x-1 transition-transform pt-4">
                  READ JOURNAL <span className="text-xs">→</span>
                </div>
              </div>
            </Link>
          ))}
        </section>

      </div>
    </div>
  );
}
