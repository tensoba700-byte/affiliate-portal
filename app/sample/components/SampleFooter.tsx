import React from 'react';
import Link from 'next/link';

export default function SampleFooter() {
  return (
    <footer className="sample-footer">
      <div className="sample-footer-inner">
        <Link href="/sample" className="sample-footer-logo">
          mikke!
        </Link>
        <p className="sample-footer-desc">
          コスメオタク美容ライター・ツキが、忙しい大人のために送る本音の検証コスメポータル。本当に崩れない・荒れない実力派だけを徹底レビュー。
        </p>
        <nav className="sample-footer-nav">
          <Link href="/sample">HOME</Link>
          <span>|</span>
          <Link href="/sample/column">COLUMN</Link>
          <span>|</span>
          <span style={{ cursor: 'not-allowed', opacity: 0.4 }}>ABOUT</span>
          <span>|</span>
          <span style={{ cursor: 'not-allowed', opacity: 0.4 }}>CONTACT</span>
        </nav>
        <p className="sample-footer-copy">
          &copy; {new Date().getFullYear()} MIKKE! ALL RIGHTS RESERVED.
        </p>
      </div>
    </footer>
  );
}
