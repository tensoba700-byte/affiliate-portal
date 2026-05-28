import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  /* config options here */
  async redirects() {
    return [
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
    ];
  },
};

export default nextConfig;
