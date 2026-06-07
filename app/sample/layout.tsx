import React from 'react';
import './sample-globals.css';

export default function SampleLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return <>{children}</>;
}
