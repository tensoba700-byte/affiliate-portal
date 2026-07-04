import type { NextConfig } from "next";

// 日本語文字を含むパスをパーセントエンコードする関数（NFC正規化も行う）
const encodePath = (p: string) => {
  return p.normalize('NFC').split('/').map(seg => {
    // コロンで始まる Next.js パラメータや、* などのワイルドカードはエンコードしない
    if (seg.startsWith(':') || seg.includes('*')) return seg;
    return seg.split('').map(c => {
      if (/[\w\-._~]/.test(c)) return c;
      return encodeURIComponent(c);
    }).join('');
  }).join('/');
};

const nextConfig: NextConfig = {
  /* config options here */
  images: {
    remotePatterns: [
      {
        protocol: 'https',
        hostname: 'thumbnail.image.rakuten.co.jp',
      },
      {
        protocol: 'https',
        hostname: '*.r10s.jp',
      },
      {
        protocol: 'https',
        hostname: 'm.media-amazon.com',
      },
      {
        protocol: 'https',
        hostname: '*.my-best.com',
      },
      {
        protocol: 'https',
        hostname: 'michill.jp',
      },
      {
        protocol: 'https',
        hostname: 'allabout.co.jp',
      },
    ],
  },
  async redirects() {
    const rawRedirects = [
      {
        source: '/articles/20260523-2026年最新絶対に焼けたくない人のための日焼け止めおすすめ',
        destination: '/articles/20260523-2026年最新日焼け止めおすすめ人気ランキング絶対に焼かない',
        permanent: true,
      },
      {
        source: '/articles/20260523-2026年最新絶対に焼けたくない人のための日焼け止めおすすめ-fix',
        destination: '/articles/20260523-2026年最新日焼け止めおすすめ人気ランキング絶対に焼かない',
        permanent: true,
      },
      {
        source: '/articles/20260524-毎日のバスタイムに上質な潤いを美容と節水を叶えるシャワーヘッ',
        destination: '/',
        permanent: true,
      },
      {
        source: '/articles/20260524-毎日のバスタイムに上質な潤いを美容と節水を叶えるシャワーヘッ-fix',
        destination: '/',
        permanent: true,
      },
      {
        source: '/articles/20260524-2026年最新シャワーヘッドおすすめ人気ランキング美容節水水',
        destination: '/',
        permanent: true,
      },
      {
        source: '/articles/20260528-frying-pans',
        destination: '/',
        permanent: true,
      },
      {
        source: '/articles/20260528-frying-pans-fix',
        destination: '/',
        permanent: true,
      },
      {
        source: '/articles/20260530-frying-pans',
        destination: '/',
        permanent: true,
      },
      {
        source: '/articles/20260601-eyeliner-comparison',
        destination: '/articles/20260603-eyeliner-comparison',
        permanent: true,
      },
      {
        source: '/articles/20260526-mac-mini-monitor-selection',
        destination: '/articles/20260526-mac-mini-monitors',
        permanent: true,
      },
      {
        source: '/articles/20260526-mac-mini-monitor-guide',
        destination: '/articles/20260526-mac-mini-monitors',
        permanent: true,
      },
      {
        source: '/articles/20260528-mac-mini-monitors',
        destination: '/articles/20260526-mac-mini-monitors',
        permanent: true,
      },
      {
        source: '/articles/20260503-料理人が静かに選ぶ本物の道具燕三条関産の本格キッチ',
        destination: '/articles/20260502-料理人が静かに選ぶ本物の道具燕三条関産の本格キッチ',
        permanent: true,
      },
      {
        source: '/articles/20260501-夜の空気を香りで塗り替えるルームフレグランス6選',
        destination: '/articles/20260505-夜の空気を香りで塗り替えるルームフレグランス6選',
        permanent: true,
      },
      {
        source: '/articles/20260526-market-shampoo-selection',
        destination: '/articles/20260526-best-shampoos-for-damaged-hair',
        permanent: true,
      },
      {
        source: '/article/20260428-tokio-ie-inkarami-review',
        destination: '/articles/20260509-髪をちゃんといたわるサロン品質ヘアケアアイテム6選',
        permanent: true,
      },
      {
        source: '/article/20260430-olaplex-no3-review',
        destination: '/articles/20260509-髪をちゃんといたわるサロン品質ヘアケアアイテム6選',
        permanent: true,
      },
      {
        source: '/article/20260429-night-hair-care-6',
        destination: '/articles/20260429-明日の朝が変わる夜の髪時間ヘアトリートメントナイト',
        permanent: true,
      },
      {
        source: '/articles/20260520-夜空の下へ持ち出したいアウトドアキャンプギア6選',
        destination: '/articles/20260519-焚き火の前の静かな時間アウトドアギア-精鋭6選',
        permanent: true,
      },
      {
        source: '/articles/20260427-2026年片付け上手になれる見せる収納隠す収納おす',
        destination: '/articles',
        permanent: true,
      },
      {
        source: '/articles/20260429-思考が加速する机の話在宅ワーカーのデスク文具6選',
        destination: '/articles',
        permanent: true,
      },
      {
        source: '/articles/20260428-肌に正直なものだけを乾燥肌敏感肌のスキンケアアイテ',
        destination: '/articles',
        permanent: true,
      },
      {
        source: '/articles/20260503-深い眠りには静かな準備がある睡眠の質を高める寝室入',
        destination: '/articles',
        permanent: true,
      },
      {
        source: '/articles/20260428-台所に手間をかけない道具を共働き家庭の時短キッチン',
        destination: '/articles',
        permanent: true,
      },
      {
        source: '/articles/20260525-灯を落としてから肌と向き合う夜就寝前ナイトケアコス',
        destination: '/articles',
        permanent: true,
      },
      {
        source: '/articles/20260502-家をもっと賢くするスマートホームデバイス6選',
        destination: '/articles',
        permanent: true,
      },
      {
        source: '/articles/20260524-肌は夜に育てる30代から始めるメンズスキンケア夜ル',
        destination: '/articles',
        permanent: true,
      },
      {
        source: '/articles/20260518-体を動かすのが楽しくなってきたフィットネスボディケ',
        destination: '/articles',
        permanent: true,
      },
      {
        source: '/articles/20260522-音で彩る自分だけの朝ポータブルスピーカーbluet',
        destination: '/articles',
        permanent: true,
      },
      {
        source: '/articles/20260508-書くことがもっと好きになるこだわりデスク文具6選',
        destination: '/articles',
        permanent: true,
      },
      {
        source: '/articles/20260519-ながら聴きをもっと豊かにワイヤレスイヤホン-こだわ',
        destination: '/articles/20260517-音で変わる朝のリズムノイズキャンセリングイヤホン-',
        permanent: true,
      },
      {
        source: '/articles/20260512-湯船でほどける夜に疲れた日の入浴グッズバスケア6選',
        destination: '/articles',
        permanent: true,
      },
      {
        source: '/articles/20260502-料理人が静かに選ぶ本物の道具燕三条関産の本格キッチ',
        destination: '/articles',
        permanent: true,
      },
      {
        source: '/articles/20260430-在宅ワークの肩こりに本気の回答を筋膜ケアボディリカ',
        destination: '/articles',
        permanent: true,
      },
      {
        source: '/column/honest-makeup-base',
        destination: '/column',
        permanent: true,
      },
      {
        source: '/column/night-pore-reset',
        destination: '/column',
        permanent: true,
      },
      {
        source: '/articles/20260616-article-001',
        destination: '/articles/20260616-face-wash',
        permanent: true,
      },
      {
        source: '/articles/20260620-article-002',
        destination: '/articles/20260620-article-001',
        permanent: true,
      },
    ];

    return rawRedirects.map(r => ({
      ...r,
      source: encodePath(r.source),
      destination: encodePath(r.destination),
    }));
  },
};

export default nextConfig;
