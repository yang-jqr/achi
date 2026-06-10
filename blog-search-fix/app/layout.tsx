import type { Metadata } from "next";
import Search from "@/components/Search";
import "./globals.css";

export const metadata: Metadata = {
  title: "GitHub Trending 笔记",
  description: "每日自动抓取 GitHub Trending，AI 分析趋势",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="zh-CN">
      <body>
        <header className="border-b border-border bg-surface">
          <div className="max-w-3xl mx-auto px-4 py-4 flex items-center justify-between gap-4">
            <a href="/" className="text-lg font-bold text-[#f0f6fc] no-underline shrink-0">
              🔥 GitHub Trending 笔记
            </a>
            <div className="flex items-center gap-3">
              <span className="text-sm text-muted hidden sm:inline">每日自动 · AI 分析</span>
              <Search />
            </div>
          </div>
        </header>
        <main className="max-w-3xl mx-auto px-4 py-8">{children}</main>
      </body>
    </html>
  );
}
