"use client";
import React, { useEffect } from 'react';
import './sample-globals.css';
import SampleHeader from './components/SampleHeader';
import SampleFooter from './components/SampleFooter';

export default function SampleLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  useEffect(() => {
    // Add class to body to hide global elements in style sheet
    document.body.classList.add('is-sample-route');
    
    // Force clean-science theme globally
    document.documentElement.setAttribute('data-theme', 'clean-science');
    
    return () => {
      document.body.classList.remove('is-sample-route');
    };
  }, []);

  return (
    <div className="clean-science-theme-wrapper min-h-screen w-full flex flex-col bg-background text-foreground">
      <SampleHeader />
      <main className="flex-1 flex flex-col w-full">
        {children}
      </main>
      <SampleFooter />
    </div>
  );
}
