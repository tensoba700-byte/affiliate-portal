"use client";

import React, { useEffect, useState, useRef } from 'react';

type AdType = 'small' | 'large';

const SMALL_ADS = [
  // 広告①
  `<a href="https://px.a8.net/svt/ejp?a8mat=4B1KXO+CLOCII+42Y0+631SX" rel="nofollow">
<img border="0" width="234" height="60" alt="" src="https://www21.a8.net/svt/bgt?aid=260414268762&wid=002&eno=01&mid=s00000019044001022000&mc=1"></a>
<img border="0" width="1" height="1" src="https://www13.a8.net/0.gif?a8mat=4B1KXO+CLOCII+42Y0+631SX" alt="">`,
  // 広告②
  `<a href="https://px.a8.net/svt/ejp?a8mat=4B1KXO+BNQN16+4X44+5ZU29" rel="nofollow">
<img border="0" width="234" height="60" alt="" src="https://www21.a8.net/svt/bgt?aid=260414268705&wid=002&eno=01&mid=s00000022954001007000&mc=1"></a>
<img border="0" width="1" height="1" src="https://www14.a8.net/0.gif?a8mat=4B1KXO+BNQN16+4X44+5ZU29" alt="">`,
  // 広告③
  `<a href="https://px.a8.net/svt/ejp?a8mat=4B1KXO+AG9ZVE+44IY+601S1" rel="nofollow">
<img border="0" width="234" height="60" alt="" src="https://www28.a8.net/svt/bgt?aid=260414268632&wid=002&eno=01&mid=s00000019249001008000&mc=1"></a>
<img border="0" width="1" height="1" src="https://www17.a8.net/0.gif?a8mat=4B1KXO+AG9ZVE+44IY+601S1" alt="">`,
  // 広告④
  `<a href="https://px.a8.net/svt/ejp?a8mat=4B1KXO+69NBTM+2SNC+64C3L" rel="nofollow">
<img border="0" width="300" height="250" alt="" src="https://www20.a8.net/svt/bgt?aid=260414268379&wid=002&eno=01&mid=s00000013044001028000&mc=1"></a>
<img border="0" width="1" height="1" src="https://www14.a8.net/0.gif?a8mat=4B1KXO+69NBTM+2SNC+64C3L" alt="">`
];

const LARGE_ADS = [
  // 広告⑤
  `<a href="https://px.a8.net/svt/ejp?a8mat=4B1KXO+9TNIVU+1RNO+6F1WH" rel="nofollow">
<img border="0" width="250" height="250" alt="" src="https://www27.a8.net/svt/bgt?aid=260414268594&wid=002&eno=01&mid=s00000008250001078000&mc=1"></a>
<img border="0" width="1" height="1" src="https://www14.a8.net/0.gif?a8mat=4B1KXO+9TNIVU+1RNO+6F1WH" alt="">`,
  // 広告⑥
  `<a href="https://px.a8.net/svt/ejp?a8mat=4B1KXO+8L00II+3PVQ+ZUAM9" rel="nofollow">
<img border="0" width="300" height="250" alt="" src="https://www22.a8.net/svt/bgt?aid=260414268519&wid=002&eno=01&mid=s00000017351006020000&mc=1"></a>
<img border="0" width="1" height="1" src="https://www15.a8.net/0.gif?a8mat=4B1KXO+8L00II+3PVQ+ZUAM9" alt="">`,
  // 広告⑦ (Script)
  `<script type='text/javascript' src='https://ad-verification.a8.net/ad/js/brandsafe.js'></script>
<div id='div_admane_async_4171_2315_10774'></div>
<script type='text/javascript'>
  if (typeof brandsafe_js_async === 'function') {
    brandsafe_js_async('//ad-verification.a8.net/ad', '_site=4171&_article=2315&_link=10774&_image=11481&sad=s00000005350011', '260414268591', '4B1KXO+9RV82I+15A4+1TIJEP');
  } else {
    // If not loaded yet, wait slightly and try again
    setTimeout(() => {
      if (typeof brandsafe_js_async === 'function') {
        brandsafe_js_async('//ad-verification.a8.net/ad', '_site=4171&_article=2315&_link=10774&_image=11481&sad=s00000005350011', '260414268591', '4B1KXO+9RV82I+15A4+1TIJEP');
      }
    }, 500);
  }
</script>
<img border="0" width="1" height="1" src="https://www16.a8.net/0.gif?a8mat=4B1KXO+9RV82I+15A4+1TIJEP" alt="">`
];

export const AdBanner: React.FC<{ type: AdType }> = ({ type }) => {
  const [adHtml, setAdHtml] = useState<string | null>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const ads = type === 'small' ? SMALL_ADS : LARGE_ADS;
    const randomIndex = Math.floor(Math.random() * ads.length);
    setAdHtml(ads[randomIndex]);
  }, [type]);

  useEffect(() => {
    if (adHtml && containerRef.current) {
      // Clear existing content
      containerRef.current.innerHTML = '';
      
      // Create a document fragment from the HTML
      const range = document.createRange();
      const fragment = range.createContextualFragment(adHtml);
      
      // Append fragment to container
      // createContextualFragment handles script execution in some browsers, 
      // but to be safe, we manually append scripts.
      containerRef.current.appendChild(fragment);
      
      // Re-run any scripts manually
      const scripts = containerRef.current.querySelectorAll('script');
      scripts.forEach((oldScript) => {
        const newScript = document.createElement('script');
        Array.from(oldScript.attributes).forEach((attr) => {
          newScript.setAttribute(attr.name, attr.value);
        });
        if (oldScript.innerHTML) {
          newScript.innerHTML = oldScript.innerHTML;
        }
        oldScript.parentNode?.replaceChild(newScript, oldScript);
      });
    }
  }, [adHtml]);

  if (!adHtml) return <div className="my-6 min-h-[60px]" />;

  return (
    <div className="w-full flex flex-col items-center justify-center my-6 animate-fade-in">
      <div className="w-full max-w-[320px] flex flex-col items-center">
        <span className="w-full text-left text-[10px] text-muted font-bold mb-1 ml-1 opacity-60">PR</span>
        <div 
          ref={containerRef}
          className="flex justify-center items-center overflow-visible rounded-[4px]"
        />
      </div>
    </div>
  );
};
