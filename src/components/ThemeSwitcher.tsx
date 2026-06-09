"use client";
import { useState, useEffect } from "react";
import { usePathname } from "next/navigation";

export default function ThemeSwitcher() {
  const pathname = usePathname();
  const [theme, setTheme] = useState("peach");
  const [font, setFont] = useState("sans");
  const [mounted, setMounted] = useState(false);
  const [open, setOpen] = useState(false);

  useEffect(() => {
    setMounted(true);
    const savedTheme = localStorage.getItem("mikke-theme") || "peach";
    const savedFont = localStorage.getItem("mikke-font") || "sans";
    setTheme(savedTheme);
    setFont(savedFont);
  }, []);

  useEffect(() => {
    // Skip theme overrides on sample route
    if (pathname?.startsWith('/sample')) return;

    if (mounted) {
      document.documentElement.setAttribute('data-theme', theme);
      document.documentElement.setAttribute('data-font', font);
      localStorage.setItem("mikke-theme", theme);
      localStorage.setItem("mikke-font", font);
    }
  }, [theme, font, mounted, pathname]);

  if (!mounted) return null;
  if (pathname?.startsWith('/sample')) return null;

  return (
    <div className="fixed bottom-4 left-4 z-50 flex flex-col items-start gap-2">

      {/* Toggle Button */}
      <button
        onClick={() => setOpen(!open)}
        className="w-10 h-10 rounded-full bg-white cute-shadow border border-card-border flex items-center justify-center text-lg hover:scale-110 transition-transform"
        title="テーマ変更"
      >
        🎨
      </button>

      {/* Panel — only visible when open */}
      {open && (
        <div className="bg-white/95 backdrop-blur-md rounded-2xl cute-shadow border border-card-border p-3 flex flex-col gap-3 w-[calc(100vw-2rem)] max-w-xs">

          {/* ✒️ フォント切り替え */}
          <div>
            <p className="text-[10px] font-black text-muted mb-2">フォント</p>
            <div className="flex gap-1 flex-wrap">
              {[
                { key: "sans", label: "ゴシック" },
                { key: "maru", label: "丸ゴシック" },
                { key: "serif", label: "明朝体" },
              ].map((f) => (
                <button
                  key={f.key}
                  onClick={() => setFont(f.key)}
                  className={`px-3 py-1 text-[11px] font-bold rounded-full transition-all ${font === f.key ? 'bg-foreground text-white' : 'text-muted hover:bg-gray-100'}`}
                >
                  {f.label}
                </button>
              ))}
            </div>
          </div>

          {/* 🎨 カラー切り替え */}
          <div>
            <p className="text-[10px] font-black text-muted mb-2">カラー</p>
            <div className="flex gap-2 flex-wrap">
              {[
                { key: "original-orange", color: "#ff5a36", label: "オレンジ" },
                { key: "peach", color: "#ff8fa3", label: "ピンク" },
                { key: "mint", color: "#4fdaab", label: "ミント" },
                { key: "lavender", color: "#a88be8", label: "ラベンダー" },
                { key: "lemon", color: "#f2ba49", label: "イエロー" },
                { key: "skyblue", color: "#76c0ff", label: "水色" },
              ].map((t) => (
                <button
                  key={t.key}
                  onClick={() => setTheme(t.key)}
                  title={t.label}
                  className={`flex-shrink-0 w-8 h-8 rounded-full border-[3px] hover:scale-110 transition-transform ${theme === t.key ? 'border-foreground shadow-lg' : 'border-white'}`}
                  style={{ backgroundColor: t.color }}
                />
              ))}
            </div>
          </div>

        </div>
      )}
    </div>
  );
}
