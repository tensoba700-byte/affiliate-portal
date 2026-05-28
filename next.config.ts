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
        source: encodeURI('/articles/20260503-料理人が静かに選ぶ本物の道具燕三条関産の本格キッチ'),
        destination: encodeURI('/articles/20260502-料理人が静かに選ぶ本物の道具燕三条関産の本格キッチ'),
        permanent: true,
      },
      {
        source: encodeURI('/articles/20260501-夜の空気を香りで塗り替えるルームフレグランス6選'),
        destination: encodeURI('/articles/20260505-夜の空気を香りで塗り替えるルームフレグランス6選'),
        permanent: true,
      },
    ];
  },
};

export default nextConfig;
