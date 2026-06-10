'use client';

import { useState, useEffect, useRef } from 'react';
import { useRouter } from 'next/navigation';

interface SearchEntry {
  slug: string;
  date: string;
  repos: string[];
  langs: string[];
  content: string;
}

export default function Search() {
  const [query, setQuery] = useState('');
  const [data, setData] = useState<SearchEntry[]>([]);
  const [results, setResults] = useState<SearchEntry[]>([]);
  const [open, setOpen] = useState(false);
  const [selected, setSelected] = useState(0);
  const containerRef = useRef<HTMLDivElement>(null);
  const router = useRouter();

  useEffect(() => {
    fetch('/search-data.json')
      .then(r => r.json())
      .then(setData)
      .catch(() => {});
  }, []);

  useEffect(() => {
    if (!query.trim()) {
      setResults([]);
      setOpen(false);
      return;
    }
    const q = query.toLowerCase();
    const filtered = data.filter(entry =>
      entry.repos.some(r => r.toLowerCase().includes(q)) ||
      entry.langs.some(l => l.toLowerCase().includes(q)) ||
      entry.date.includes(q) ||
      entry.slug.toLowerCase().includes(q) ||
      entry.content.toLowerCase().includes(q)
    ).slice(0, 10);
    setResults(filtered);
    setOpen(filtered.length > 0);
    setSelected(0);
  }, [query, data]);

  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setOpen(false);
      }
    };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, []);

  const handleKey = (e: React.KeyboardEvent) => {
    if (!open) return;
    if (e.key === 'ArrowDown') { e.preventDefault(); setSelected(s => Math.min(s + 1, results.length - 1)); }
    if (e.key === 'ArrowUp') { e.preventDefault(); setSelected(s => Math.max(s - 1, 0)); }
    if (e.key === 'Enter' && results[selected]) {
      router.push(`/posts/${encodeURIComponent(results[selected].slug)}`);
      setOpen(false);
      setQuery('');
    }
    if (e.key === 'Escape') setOpen(false);
  };

  return (
    <div ref={containerRef} className="relative w-48 sm:w-56">
      <input
        type="text"
        placeholder="搜索仓库、内容、日期…"
        value={query}
        onChange={e => setQuery(e.target.value)}
        onKeyDown={handleKey}
        onFocus={() => { if (results.length > 0) setOpen(true); }}
        className="w-full px-3 py-1.5 text-sm bg-[#0d1117] border border-border rounded-md text-[#c9d1d9] placeholder:text-muted focus:outline-none focus:border-accent transition-colors"
      />
      {open && (
        <div className="absolute top-full mt-1 left-0 right-0 bg-surface border border-border rounded-md shadow-lg z-50 max-h-80 overflow-y-auto">
          {results.map((entry, i) => (
            <button
              key={entry.slug}
              onClick={() => {
                router.push(`/posts/${encodeURIComponent(entry.slug)}`);
                setOpen(false);
                setQuery('');
              }}
              className={`w-full text-left px-3 py-2.5 text-sm border-b border-border last:border-0 transition-colors ${
                i === selected ? 'bg-accent/10 text-[#f0f6fc]' : 'text-[#c9d1d9] hover:bg-[#1c2128]'
              }`}
            >
              <div className="font-semibold text-accent text-xs mb-1">{entry.date}</div>
              <div className="flex flex-wrap gap-1 items-center mb-1">
                {entry.repos.slice(0, 3).map(r => (
                  <span key={r} className="px-1.5 py-0.5 bg-[#0d1117] border border-border rounded text-xs text-muted">{r}</span>
                ))}
                {entry.repos.length > 3 && <span className="text-xs text-muted">+{entry.repos.length - 3}</span>}
                {entry.langs.length > 0 && (
                  <span className="text-xs text-muted ml-1">{entry.langs.slice(0, 2).join(' · ')}</span>
                )}
              </div>
              {entry.content && (
                <div className="text-xs text-muted leading-relaxed line-clamp-2">
                  {entry.content.slice(0, 150)}
                </div>
              )}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
