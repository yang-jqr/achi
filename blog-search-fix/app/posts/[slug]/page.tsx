import { getPost, getAllPosts, resolveWikiLinks, extractLanguages, extractRepoNames } from "@/lib/posts";
import { notFound } from "next/navigation";
import Link from "next/link";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

export function generateStaticParams() {
  return getAllPosts().map(p => ({ slug: p.meta.slug }));
}

export default async function PostPage({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;
  const decodedSlug = decodeURIComponent(slug);
  const post = getPost(decodedSlug);
  if (!post) notFound();
  const allSlugs = new Set(getAllPosts().map(p => p.meta.slug));
  const text = resolveWikiLinks(post.content, allSlugs);
  const all = getAllPosts();
  const i = all.findIndex(p => p.meta.slug === decodedSlug);
  const prev = i < all.length - 1 ? all[i + 1] : null;
  const next = i > 0 ? all[i - 1] : null;
  const langs = extractLanguages(post.content);
  const names = extractRepoNames(post.content);

  return (
    <article>
      <div className="flex items-center justify-between mb-6 text-sm">
        <Link href="/" className="text-muted hover:text-accent transition-colors">← 全部笔记</Link>
        <div className="flex gap-3">
          {prev && <Link href={`/posts/${encodeURIComponent(prev.meta.slug)}`} className="text-accent hover:underline">← {prev.meta.date||prev.meta.slug}</Link>}
          {next && <Link href={`/posts/${encodeURIComponent(next.meta.slug)}`} className="text-accent hover:underline">{next.meta.date||next.meta.slug} →</Link>}
        </div>
      </div>
      <div className="mb-6">
        <div className="flex flex-wrap items-center gap-3 mb-3">
          {langs.slice(0, 4).map(l => (
            <span key={l} className="px-2.5 py-1 bg-accent/10 text-accent border border-accent/20 rounded-full text-xs">{l}</span>
          ))}
        </div>
        <h1 className="text-2xl font-bold text-[#f0f6fc]">GitHub Trending — {post.meta.date}</h1>
        <div className="flex gap-4 mt-2 text-sm text-muted">
          <span>{names.length} 个仓库</span>
          <span>{langs.length} 种语言</span>
        </div>
      </div>
      <div className="prose prose-invert max-w-none">
        <ReactMarkdown remarkPlugins={[remarkGfm]} components={{
          a: ({href,children,...p}) => <a href={href} target={href?.startsWith("http")?"_blank":undefined} rel={href?.startsWith("http")?"noopener noreferrer":undefined} className="text-accent hover:underline" {...p}>{children}</a>,
          del: ({children}) => <span className="text-muted line-through">{children}</span>,
          pre: ({children}) => <pre className="bg-[#0d1117] border border-border rounded-lg p-4 overflow-x-auto text-sm leading-relaxed">{children}</pre>,
          code: ({className,children,...p}) => !className ? <code className="bg-[#0d1117] border border-border rounded px-1.5 py-0.5 text-sm text-[#c9d1d9]" {...p}>{children}</code> : <code className={className} {...p}>{children}</code>,
          hr: () => <hr className="border-border my-8" />,
          h2: ({children}) => <h2 className="text-lg font-semibold text-[#f0f6fc] mt-8 mb-4 pb-2 border-b border-border">{children}</h2>,
          strong: ({children}) => <strong className="text-[#f0f6fc]">{children}</strong>,
        }}>{text}</ReactMarkdown>
      </div>
      <div className="mt-10 pt-4 border-t border-border">
        <div className="flex justify-between text-sm">
          {prev ? <Link href={`/posts/${encodeURIComponent(prev.meta.slug)}`} className="text-accent hover:underline">← {prev.meta.date}</Link> : <span />}
          {next ? <Link href={`/posts/${encodeURIComponent(next.meta.slug)}`} className="text-accent hover:underline">{next.meta.date} →</Link> : <span />}
        </div>
        <div className="text-center mt-6">
          <Link href="/" className="text-muted hover:text-accent text-sm transition-colors">← 返回首页</Link>
        </div>
      </div>
    </article>
  );
}