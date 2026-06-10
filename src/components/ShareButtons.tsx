"use client";

type Props = {
  url: string;
  title: string;
  isGadget?: boolean;
};

const BUTTONS = [
  {
    key: "x",
    label: "X",
    color: "#000000",
    share: (url: string, title: string, isGadget?: boolean) => {
      const text = isGadget 
        ? `🔥 これ、マジでおすすめ！\n\n「${title}」\n\n徹底比較で見つけた最強ガジェットをチェックしよう 🚀⚡️\n#ガジェット #レビュー #みっけ`
        : `✨ めっちゃ気になる！\n\n「${title}」\n\nみっけ！で見つけたよ 🎀💕\n#みっけ #おすすめ`;
      return `https://twitter.com/intent/tweet?text=${encodeURIComponent(text)}&url=${encodeURIComponent(url)}`;
    },
  },
  {
    key: "facebook",
    label: "f",
    color: "#1877F2",
    share: (url: string) =>
      `https://www.facebook.com/sharer/sharer.php?u=${encodeURIComponent(url)}`,
  },
  {
    key: "line",
    label: "L",
    color: "#06C755",
    share: (url: string, title: string, isGadget?: boolean) => {
      const text = isGadget
        ? `🚀 ガジェット選びの決定版！✨\n「${title}」\n実際に使って分かった本気のおすすめ！💡`
        : `🎀 これ良さそう！✨\n「${title}」\nみっけ！で見つけたよ💕`;
      return `https://social-plugins.line.me/lineit/share?url=${encodeURIComponent(url)}&text=${encodeURIComponent(text)}`;
    },
  },
  {
    key: "threads",
    label: "@",
    color: "#000000",
    share: (url: string, title: string, isGadget?: boolean) => {
      const text = isGadget
        ? `💻 最新レビュー公開！\n\n「${title}」\n\nこれは買い。スペックも機能性も最高でした 🚀⚡️\n${url}`
        : `🌸 おすすめ見つけた！\n\n「${title}」\n\nめっちゃ良さそう…！🎀✨\n${url}`;
      return `https://www.threads.net/intent/post?text=${encodeURIComponent(text)}`;
    },
  },
];

export default function ShareButtons({ url, title, isGadget }: Props) {
  return (
    <div className="mt-16 pt-8 border-t border-primary/10 flex flex-col items-center">
      <p className="text-xs font-black text-muted mb-4">この記事をシェアする 💭</p>
      <div className="flex justify-center gap-3">
        {BUTTONS.map((btn) => (
          <a
            key={btn.key}
            href={btn.share(url, title, isGadget)}
            target="_blank"
            rel="noopener noreferrer"
            className="w-10 h-10 rounded-[4px] flex items-center justify-center hover:opacity-80 hover:-translate-y-1 transition-all font-black text-white text-sm shadow-sm"
            style={{ background: btn.color }}
            title={btn.label}
          >
            {btn.label}
          </a>
        ))}
      </div>
    </div>
  );
}
