"use client";
import React, { useEffect, useState } from 'react';
import './sample-globals.css';
import SampleHeader from './components/SampleHeader';
import SampleFooter from './components/SampleFooter';

export default function SampleLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const [theme, setTheme] = useState<'clean-science' | 'korean-cafe'>('clean-science');

  useEffect(() => {
    // Add class to body to hide global elements in style sheet
    document.body.classList.add('is-sample-route');
    
    // Load saved theme
    try {
      const saved = localStorage.getItem('sample-theme') as 'clean-science' | 'korean-cafe';
      if (saved === 'korean-cafe' || saved === 'clean-science') {
        setTheme(saved);
      }
    } catch (e) {}
    
    return () => {
      document.body.classList.remove('is-sample-route');
      document.body.classList.remove('clean-science-theme');
      document.body.classList.remove('korean-cafe-theme');
    };
  }, []);

  useEffect(() => {
    try {
      if (theme === 'korean-cafe') {
        document.documentElement.setAttribute('data-theme', 'korean-cafe');
        document.body.classList.add('korean-cafe-theme');
        document.body.classList.remove('clean-science-theme');
      } else {
        document.documentElement.setAttribute('data-theme', 'clean-science');
        document.body.classList.add('clean-science-theme');
        document.body.classList.remove('korean-cafe-theme');
      }
    } catch (e) {}
  }, [theme]);

  const toggleTheme = () => {
    const next = theme === 'clean-science' ? 'korean-cafe' : 'clean-science';
    setTheme(next);
    try {
      localStorage.setItem('sample-theme', next);
    } catch (e) {}
  };

  const wrapperClass = theme === 'korean-cafe' ? 'korean-cafe-theme-wrapper' : 'clean-science-theme-wrapper';

  return (
    <div className={`${wrapperClass} min-h-screen w-full flex flex-col bg-background text-foreground`}>
      {/* Inline script to prevent flash */}
      <script dangerouslySetInnerHTML={{
        __html: `
          try {
            var saved = localStorage.getItem('sample-theme');
            if (saved === 'korean-cafe') {
              document.documentElement.setAttribute('data-theme', 'korean-cafe');
              document.body.classList.add('korean-cafe-theme');
              document.body.classList.remove('clean-science-theme');
            } else {
              document.documentElement.setAttribute('data-theme', 'clean-science');
              document.body.classList.add('clean-science-theme');
              document.body.classList.remove('korean-cafe-theme');
            }
          } catch (e) {}
        `
      }} />
      <SampleHeader currentTheme={theme} onToggleTheme={toggleTheme} />
      <main className="flex-1 flex flex-col w-full">
        {children}
      </main>
      <SampleFooter />
    </div>
  );
}

