const fs = require('fs');
const path = require('path');
const matter = require('gray-matter');

const contentDir = path.resolve(__dirname, '..', 'content');
const outputPath = path.resolve(__dirname, '..', 'public', 'search-data.json');

const results = [];

if (!fs.existsSync(contentDir)) {
  console.warn('Content directory not found, generating empty search index');
  fs.mkdirSync(path.dirname(outputPath), { recursive: true });
  fs.writeFileSync(outputPath, '[]');
  process.exit(0);
}

const files = fs.readdirSync(contentDir).filter(f => f.endsWith('.md'));

for (const file of files) {
  const slug = file.replace(/\.md$/, '');
  const raw = fs.readFileSync(path.join(contentDir, file), 'utf-8');
  const { data } = matter(raw);
  const m = slug.match(/trending-(\d{4}-\d{2}-\d{2})/);
  const date = m ? m[1] : data.date || '';

  const repos = [];
  const langs = new Set();

  for (const line of raw.split('\n')) {
    let rm = line.match(/^## \d+\. (.+)/);
    if (!rm) rm = line.match(/^\*\*\d+\. (.+?)\*\*/);
    if (rm) {
      const name = rm[1].trim().replace(/\s*⭐.*$/, '').trim();
      if (name && name.length > 2) repos.push(name);
    }

    let lm = line.match(/⭐[^|]+\|[^|]*\|\s*(\w[\w\s+#.-]*)/);
    if (!lm) lm = line.match(/today\s*\|\s*(\w[\w+#.-]+)/);
    if (lm) {
      const lang = lm[1].trim();
      if (lang && /^[A-Z]/.test(lang) && lang.length < 20) langs.add(lang);
    }
  }

  // 提取正文纯文本（去 markdown 语法），最多 1000 字符
  const content = raw
    .replace(/^---[\s\S]*?---/, '')     // 去 frontmatter
    .replace(/#{1,6}\s+/g, '')          // 去标题标记
    .replace(/\*\*([^*]+)\*\*/g, '$1')  // 去加粗
    .replace(/\*([^*]+)\*/g, '$1')      // 去斜体
    .replace(/`{1,3}[^`]*`{1,3}/g, '') // 去行内代码
    .replace(/\[([^\]]+)\]\([^)]+\)/g, '$1') // 链接->纯文本
    .replace(/!\[([^\]]*)\]\([^)]+\)/g, '') // 去图片
    .replace(/\n{2,}/g, '\n')           // 合并空行
    .replace(/\n/g, ' ')                // 换行转空格
    .replace(/\s{2,}/g, ' ')            // 合并空格
    .trim()
    .slice(0, 1000);

  results.push({ slug, date, repos, langs: Array.from(langs), content });
}

fs.mkdirSync(path.dirname(outputPath), { recursive: true });
fs.writeFileSync(outputPath, JSON.stringify(results));
console.log(`Generated search index: ${results.length} posts`);
