import Link from 'next/link';
import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'ツキ | みっけ！専属ライター',
  description: 'コスメ・スキンケア成分の調査と比較記事を専門とするリサーチライター。成分情報・処方設計・メーカー公表データを読み解き、読者が自分に合う製品を選ぶための判断材料を提供することを使命としています。',
};

export default function AuthorTsukiPage() {
  return (
    <div className="s-col-detail s-article-page py-12 px-4 md:px-0">
      <div className="max-w-2xl mx-auto">
        <h1 className="text-2xl md:text-3xl font-black text-center mb-8" style={{ fontFamily: 'var(--s-font-serif)', color: 'var(--s-ink)' }}>
          著者プロフィール
        </h1>

        {/* Writer Profile Card */}
        <div className="s-profile-card p-6 md:p-8 bg-white rounded-lg border border-card-border cute-shadow mb-8 flex flex-col md:flex-row gap-4 items-center md:items-start">
          <div className="s-profile-avatar text-4xl p-2 bg-background rounded-full">👩🏻‍💻</div>
          <div className="flex-1">
            <div className="s-profile-name text-lg md:text-xl font-bold mb-2">
              ツキ（みっけ！専属ライター）
              <span className="s-profile-badge ml-2 text-xs bg-primary text-white px-2 py-0.5 rounded">ライター</span>
            </div>
            <p className="s-profile-desc text-sm md:text-base text-foreground/80 leading-relaxed">
              コスメ・スキンケア成分の調査と比較記事を専門とするリサーチライター。成分情報・処方設計・メーカー公表データを読み解き、読者が自分に合う製品を選ぶための判断材料を提供することを使命としています。
            </p>
          </div>
        </div>

        {/* Links */}
        <div className="text-center mt-8">
          <Link
            href="/articles/"
            className="inline-block px-6 py-3 bg-primary text-white font-bold rounded-lg cute-shadow hover:opacity-90 transition-opacity"
          >
            👉 担当記事一覧を見る
          </Link>
        </div>
      </div>
    </div>
  );
}
