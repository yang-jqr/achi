import { getAllPosts, getStats, extractRepoNames, extractLanguages, type Post } from "@/lib/posts";
import Link from "next/link";

export default function HomePage() {
  const posts = getAllPosts().filter(p => p.meta.date); // 只显示 trending 笔记
  const stats = getStats();

  return (
    <div>
      {/* Hero */}
      <section className="mb-10">
        <h1 className="text-3xl font-bold text-[#f0f6fc] mb-3">🔥 GitHub Trending 学习笔记</h1>
        <p className="text-muted text-base mb-6 max-w-xl leading-relaxed">
          每日自动抓取 GitHub 热榜前 10，AI 分析技术趋势与学习价值。
        </p>
        <div className="grid grid-cols-3 sm:grid-cols-4 gap-3">
          <StatCard value={stats.totalDays} label="天记录" />
          <StatCard value={stats.totalRepos} label="个仓库" />
          <StatCard value={stats.uniqueRepos} label="去重仓库" />
          <StatCard value={stats.recurringRepos.length} label="多次上榜" />
        </div>
      </section>

      {/* 语言标签 */}
      {stats.topLanguages.length > 0 && (
        <section className="mb-8">
          <div className="flex flex-wrap gap-2">
            {stats.topLanguages.map(({ lang, count }) => (
              <span key={lang} className="px-3 py-1 bg-surface border border-border rounded-full text-sm text-muted">
                {lang} <span className="text-accent">{count}</span>
              </span>
            ))}
          </div>
        </section>
      )}

      {/* 笔记卡片 */}
      <section>
        <h2 className="text-lg font-semibold text-[#f0f6fc] mb-4">📅 按日期浏览</h2>
        {posts.length === 0 && <p className="text-muted text-sm">暂无笔记…</p>}
        <div className="space-y-4">
          {posts.map(post => <PostCard key={post.meta.slug} post={post} />)}
        </div>
      </section>

      {/* 热门仓库 */}
      {stats.recurringRepos.length > 0 && (
        <section className="mt-10">
          <h2 className="text-lg font-semibold text-[#f0f6fc] mb-4">🔁 反复上榜</h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
            {stats.recurringRepos.slice(0, 8).map(repo => (
              <div key={repo.name} className="flex items-center justify-between bg-surface border border-border rounded-md px-3 py-2 text-sm">
                <span className="text-accent truncate mr-2">{repo.name}</span>
                <span className="text-muted shrink-0">{repo.count} 次</span>
              </div>
            ))}
          </div>
        </section>
      )}
    </div>
  );
}

function StatCard({ value, label }: { value: number; label: string }) {
  return (
    <div className="bg-surface border border-border rounded-lg px-4 py-3 text-center">
      <div className="text-2xl font-bold text-accent">{value}</div>
      <div className="text-xs text-muted mt-0.5">{label}</div>
    </div>
  );
}

function PostCard({ post }: { post: Post }) {
  const names = extractRepoNames(post.content);
  const langs = extractLanguages(post.content);
  const preview = names.slice(0, 3);

  return (
    <Link
      href={`/posts/${encodeURIComponent(post.meta.slug)}`}
      className="block bg-surface border border-border rounded-lg p-5 hover:border-accent hover:shadow-lg hover:shadow-accent/5 transition-all group"
    >
      <div className="flex items-start justify-between mb-3">
        <div>
          <span className="text-[#f0f6fc] font-semibold text-lg group-hover:text-accent transition-colors">
            {post.meta.date && `GitHub Trending — ${post.meta.date}`}
          </span>
          <div className="text-muted text-sm mt-1">{names.length} 个仓库上榜</div>
        </div>
        <div className="flex gap-1.5 shrink-0">
          {langs.slice(0, 3).map(l => (
            <span key={l} className="px-2 py-0.5 bg-[#0d1117] border border-border rounded text-xs text-muted">
              {l}
            </span>
          ))}
        </div>
      </div>
      {preview.length > 0 && (
        <div className="flex flex-wrap gap-2">
          {preview.map((name, i) => (
            <span key={name} className={`px-2 py-1 rounded text-xs ${
              i === 0 ? 'bg-accent/10 text-accent border border-accent/20' : 'bg-[#0d1117] text-muted border border-border'
            }`}>
              {name}
            </span>
          ))}
          {names.length > 3 && <span className="px-2 py-1 text-xs text-muted">+{names.length - 3}</span>}
        </div>
      )}
    </Link>
  );
}