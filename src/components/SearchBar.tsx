"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";

export default function SearchBar() {
  const [query, setQuery] = useState("");
  const router = useRouter();

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (query.trim()) {
      router.push(`/search?q=${encodeURIComponent(query.trim())}`);
    }
  };

  return (
    <form onSubmit={handleSearch} className="w-full relative group">
      <input 
        type="text" 
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        placeholder="なにをお探しですか？" 
        className="w-full bg-white border-2 border-primary/20 hover:border-primary/40 focus:border-primary rounded-full py-2.5 pl-5 pr-10 text-sm focus:outline-none transition-all duration-300 font-bold text-foreground placeholder-muted"
      />
      <button 
        type="submit" 
        className="absolute right-4 top-1/2 -translate-y-1/2 text-primary/60 hover:text-primary transition-colors cursor-pointer"
        aria-label="検索する"
      >
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round">
          <circle cx="11" cy="11" r="8"></circle>
          <line x1="21" y1="21" x2="16.65" y2="16.65"></line>
        </svg>
      </button>
    </form>
  );
}
