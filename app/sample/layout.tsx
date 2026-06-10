import React from 'react';
import './sample-globals.css';
import SampleHeader from './components/SampleHeader';
import SampleFooter from './components/SampleFooter';

export default function SampleLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="sample-wrapper min-h-screen w-full flex flex-col">
      <SampleHeader />
      <main className="flex-1 flex flex-col w-full">
        {children}
      </main>
      <SampleFooter />
    </div>
  );
}
