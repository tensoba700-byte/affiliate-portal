"use client";

import { useState, useEffect } from "react";

export default function CookieConsent() {
  const [showBanner, setShowBanner] = useState(false);

  useEffect(() => {
    const consent = localStorage.getItem("cookie-consent");
    if (!consent) {
      setShowBanner(true);
    }
  }, []);

  const handleAccept = () => {
    localStorage.setItem("cookie-consent", "true");
    setShowBanner(false);
  };

  if (!showBanner) return null;

  return (
    <div className="fixed bottom-6 left-6 right-6 md:left-auto md:right-8 md:max-w-md z-[100] animate-fade-in-up">
      <div className="bg-white rounded-[2rem] p-6 cute-shadow border-2 border-primary/20 flex flex-col gap-4 relative overflow-hidden">
        {/* Decorative elements */}
        <div className="absolute -top-4 -right-4 w-12 h-12 bg-primary/10 rounded-full"></div>
        
        <div className="flex items-center gap-3">
          <span className="text-2xl">🍪</span>
          <h3 className="text-sm font-black text-foreground">Cookieの使用について</h3>
        </div>
        
        <p className="text-[11px] font-bold text-muted leading-relaxed">
          みっけ！では、より良いサービス提供のためCookieを使用しています。
          サイトの閲覧を続けることで、Cookieの使用に同意したことになります。
        </p>
        
        <button
          onClick={handleAccept}
          className="w-full bg-primary text-white text-xs font-black py-3 rounded-full hover:scale-105 active:scale-95 transition-all shadow-lg shadow-primary/20"
        >
          OK、わかった！
        </button>
      </div>
    </div>
  );
}
