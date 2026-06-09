import React from 'react';
import Link from 'next/link';

export default function SampleFooter() {
  return (
    <footer className="w-full border-t border-card-border bg-zinc-50 py-12 mt-auto">
      <div className="container mx-auto max-w-4xl px-4 flex flex-col items-center gap-6">
        <Link href="/sample" className="text-lg font-black tracking-widest text-foreground font-mono">
          mikke!
        </Link>
        <p className="text-[10px] text-muted font-bold text-center tracking-wider max-w-sm leading-relaxed">
          コスメオタク美容ライター・ツキが、忙しい大人のために送る本音の検証コスメポータル「みっけ！」。本当に崩れない・荒れない実力派だけを徹底レビュー。
        </p>
        <div className="flex gap-6 text-[10px] text-muted font-bold tracking-widest uppercase">
          <Link href="/sample" className="hover:text-foreground transition-colors">HOME</Link>
          <Link href="/sample/column" className="hover:text-foreground transition-colors">COLUMN</Link>
          <span className="text-zinc-200">|</span>
          <span className="text-zinc-400 cursor-not-allowed">ABOUT</span>
          <span className="text-zinc-400 cursor-not-allowed">CONTACT</span>
        </div>
        <p className="text-[8px] text-zinc-400 font-mono tracking-widest mt-4">
          &copy; {new Date().getFullYear()} MIKKE! ALL RIGHTS RESERVED.
        </p>
      </div>
    </footer>
  );
}
