import Link from 'next/link';
import { notFound } from 'next/navigation';
import { columnsData } from '../page';

export async function generateStaticParams() {
  return [
    { slug: 'night-pore-reset' },
    { slug: 'honest-makeup-base' },
    { slug: 'morning-three-minute-glow' }
  ];
}

interface PageProps {
  params: Promise<{ slug: string }>;
}

export default async function SampleColumnDetail({ params }: PageProps) {
  const { slug } = await params;
  const column = columnsData.find(c => c.slug === slug);

  if (!column) {
    notFound();
  }

  // Next Column logic
  const currentIndex = columnsData.findIndex(c => c.slug === slug);
  const nextColumn = columnsData[(currentIndex + 1) % columnsData.length];

  const columnContents: Record<string, string> = {
    'night-pore-reset': `
      <p class="editorial-lead">ねえ、毎日仕事や家事、趣味でバタバタ大忙しで、夜にふと鏡を見て「毛穴が目立ってる…」って絶望したことない？笑</p>
      <p>日中は忙しすぎてメイク直しをする暇なんて1秒もないから、夜のクレンジング前の10分間でどれだけリセットできるかが、実は美肌キープの勝負どころなんだよね。</p>
      
      <h2>// 1. 帰宅後すぐの「温感スチームホグシ」</h2>
      <p>帰ってきてすぐクレンジングを馴染ませる前に、まずはぬるま湯で濡らして軽く絞った温タオルを顔に乗せてみて。タオルの熱で、カチコチに固まった角質や毛穴に詰まった皮脂汚れをじんわりと緩めてあげるの。この1分間があるだけで、その後のバームやオイルの馴染み方が全然違うんだよね！</p>
      
      <h2>// 2. 擦らない「とろとろ乳化クレンジング」</h2>
      <p>毛穴汚れを落としようとして指先でゴシゴシ擦るのは絶対にNG！クレンジングバームやオイルをお肌に乗せたら、体温でとろけるのを待ってから優しく円を描くように滑らせるだけ。洗い流す前に、数滴のぬるま湯を顔全体に馴染ませて白く濁らせる「乳化」を挟むと、ぬるつきを残さずにスッキリ落とせるよ。</p>
      
      <h2>// 3. 洗い上がりは「タオルで擦らず水気を吸い取る」</h2>
      <p>最後のお約束は、タオルで顔をゴシゴシ拭かないこと笑 タオルをそっとお肌に押し当てて、水気だけを吸い取らせるようにしてね。忙しい毎日だからこそ、夜のファーストステップだけは丁寧にいたわって、すっきりモチモチの美肌を一緒にキープしようね！</p>
    `,
    'honest-makeup-base': `
      <p class="editorial-lead">「崩れない！」「テカらない！」って謳う下地は世の中にたくさん溢れてるけれど、本当に夕方までキレイな状態をキープできる下地って、実は一握りだよね。</p>
      <p>今回は、日中に化粧直しをする時間が一切ない大忙しな私が、実際に使い比べて見出した「崩れない下地」の本音の選び方をまとめたよ！</p>
      
      <h2>// 1. TゾーンとUゾーンで「役割を分ける」のが鉄則</h2>
      <p>顔全体に同じ皮脂崩れ防止下地を塗って、カサカサに乾燥しちゃった経験ない？笑 脂っぽくなりやすいおでこや鼻先（Tゾーン）には皮脂吸着タイプを薄く伸ばし、乾燥しやすい目元や頬（Uゾーン）には高保湿の美容液下地を仕込むのが、実は一番崩れない方法んだよね。</p>
      
      <h2>// 2. 「毛穴の凹凸」を埋めるシリコン系は薄く叩き込む</h2>
      <p>毛穴をフラットに見せてくれるポアプライマーは便利だけど、塗りすぎると逆にファンデのヨレの原因になっちゃう。米粒半分くらいの量を指先にとって、毛穴が気になる部分にぽんぽんと優しく叩き込むように馴染ませるのがコツだよ！</p>
      
      <h2>// 3. 美容液成分が入っているかチェックしよう</h2>
      <p>皮脂を止める力が強すぎるとお肌の水分が奪われて、逆に過剰な皮脂が出て崩れてしまうことも。ヒアルロン酸やセラミドなどの美容液成分がしっかり入った、水分と皮脂のバランスを崩さないアイテムを選ぶのが、オタクの結論だよ！</p>
    `,
    'morning-three-minute-glow': `
      <p class="editorial-lead">1分1秒が惜しい朝のバタバタタイム、スキンケアを丁寧にやってる時間なんてないよね笑</p>
      <p>朝の保湿が適当だと、お昼過ぎにはファンデがカサカサに乾いて砂漠化しちゃう…そんな悩みを解決する、3分間で極上のツヤ肌を作る時短保湿メソッドを紹介するよ！</p>
      
      <h2>// 1. 化粧水バシャバシャの代わりに「プチプラ大容量パック」</h2>
      <p>朝起きて洗顔したら、すぐに大容量のプチプラシートマスクをピタッと顔に乗せるだけ！手でパッティングする手間が省けるし、パックしている3分間の間に着替えたり髪を整えたりできるから効率的。プチプラだから毎日罪悪感なく使えるのも最高だよね笑</p>
      
      <h2>// 2. パックの上から「乳液を重ねて密封」</h2>
      <p>シートマスクをはがす前に、パックの上から乳液を薄く全体に塗っちゃうの。その状態でマスクを折りたたんでパッティングしながらはがすと、化粧水の水分と乳液の油分が一気にお肌に馴染んで、もちもちのうるおいヴェールが完成するよ！</p>
      
      <h2>// 3. べたつく余分な水分はティッシュオフ</h2>
      <p>保湿しすぎて顔がベタベタのままメイクに入ると、ファンデがヨレる原因に。スキンケアが終わったら、ティッシュを顔に乗せて軽く手のひらで押さえ、表面に残った余分な油分だけをオフしてね。このひと手間で、夕方まで崩れない極上の土台が完成するよ！</p>
    `
  };

  return (
    <div className="w-full pb-32 bg-background text-foreground min-h-screen relative overflow-x-hidden">
      {/* Force clean-science theme dynamically */}
      <script dangerouslySetInnerHTML={{
        __html: `
          document.documentElement.setAttribute('data-theme', 'clean-science');
          document.documentElement.setAttribute('data-font', 'sans');
        `
      }} />

      {/* Ambient decorative glow */}
      <div className="absolute top-0 left-1/2 -translate-x-1/2 w-full max-w-7xl h-[400px] bg-gradient-to-b from-zinc-200/30 to-transparent pointer-events-none blur-3xl z-0" />

      <div className="container mx-auto max-w-2xl px-4 pt-10 relative z-10">
        
        {/* Navigation Breadcrumbs */}
        <nav className="text-[10px] font-bold mb-8 flex items-center justify-start gap-2 text-muted tracking-widest uppercase">
          <Link href="/sample" className="hover:text-primary transition-colors">HOME</Link>
          <span className="text-zinc-400">/</span>
          <Link href="/sample/column" className="hover:text-primary transition-colors">JOURNAL</Link>
          <span className="text-zinc-400">/</span>
          <span className="text-foreground truncate max-w-[150px] md:max-w-none text-left" aria-current="page">
            {column.category}
          </span>
        </nav>

        {/* Column Header */}
        <header className="bg-white rounded-2xl p-6 md:p-12 border border-card-border shadow-sm mb-8 text-center relative overflow-hidden">
          <span className="text-[9px] font-black tracking-widest text-muted block mb-4 uppercase font-mono">
            ✦ BEAUTY JOURNAL ESSAY
          </span>
          <h1 className="text-lg md:text-2xl font-black text-foreground leading-snug mb-6 tracking-tight">
            {column.title}
          </h1>
          <div className="flex items-center justify-center gap-4 text-[10px] font-bold text-muted pt-4 border-t border-zinc-50">
            <span>✍️ WRITTEN BY: カナ</span>
            <span>🗓 {column.date}</span>
          </div>
        </header>

        {/* Column Photo Area */}
        <div 
          className="w-full aspect-[21/10] rounded-2xl overflow-hidden border border-card-border shadow-sm mb-8 bg-cover bg-center"
          style={{ backgroundImage: `url(${column.coverImage})` }}
        />

        {/* Main Column Body */}
        <article 
          className="bg-white rounded-2xl p-6 md:p-12 border border-card-border shadow-sm mb-8 cute-html-content leading-relaxed"
          dangerouslySetInnerHTML={{ __html: columnContents[slug] || '' }}
        />

        {/* Beauty Writer Profile Card (Persona Match) */}
        <div className="bg-white rounded-2xl p-6 md:p-8 border border-card-border shadow-sm mb-8 flex flex-col sm:flex-row gap-5 items-center sm:items-start">
          <div className="w-16 h-16 rounded-full bg-zinc-100 border border-zinc-200 flex-shrink-0 flex items-center justify-center text-3xl shadow-inner">
            👩🏻‍💻
          </div>
          <div className="text-center sm:text-left space-y-2">
            <div className="flex flex-col sm:flex-row sm:items-center gap-1.5 justify-center sm:justify-start">
              <span className="text-sm font-black text-foreground">カナ（みっけ！専属美容ライター）</span>
              <span className="bg-zinc-100 text-zinc-800 text-[8px] font-black px-2 py-0.5 rounded-full w-fit mx-auto sm:mx-0">
                ライター
              </span>
            </div>
            <p className="text-xs text-muted leading-relaxed font-bold">
              仕事も趣味も毎日バタバタ大忙しで、日中に化粧直しをする暇なんて全くないけれど、コスメへの愛だけは誰にも負けない20代後半の等身大オタク。実生活で使い倒した「時短」「夕方に崩れない」リアルな体験談をコラムでお届けします。
            </p>
          </div>
        </div>

        {/* Next Read Recommendation */}
        <div className="bg-zinc-950 text-white rounded-2xl p-6 md:p-8 border border-zinc-900 shadow-md mb-8 flex flex-col md:flex-row items-center justify-between gap-6 transition-all duration-300 hover:bg-zinc-900">
          <div className="flex-1 space-y-2">
            <span className="inline-block bg-white/10 text-white px-2 py-0.5 rounded text-[8px] font-bold tracking-widest uppercase">
              NEXT JOURNAL
            </span>
            <h3 className="text-sm md:text-base font-black leading-snug tracking-tight">
              {nextColumn.title}
            </h3>
            <Link 
              href={`/sample/column/${nextColumn.slug}`}
              className="inline-flex items-center gap-1 text-xs font-black pt-2 text-white border-b border-white/30 hover:border-white transition-all"
            >
              コラムを読む →
            </Link>
          </div>
          <div 
            className="w-full md:w-24 aspect-video md:aspect-square bg-cover bg-center rounded-xl flex-shrink-0 border border-white/10"
            style={{ backgroundImage: `url(${nextColumn.coverImage})` }}
          />
        </div>

        {/* Back Link */}
        <div className="text-center pt-4">
          <Link 
            href="/sample/column" 
            className="inline-flex items-center gap-2 bg-white hover:bg-zinc-50 border border-card-border rounded-full px-8 py-3 text-xs font-black transition-all shadow-sm"
          >
            ← コラム一覧に戻る
          </Link>
        </div>

      </div>
    </div>
  );
}
