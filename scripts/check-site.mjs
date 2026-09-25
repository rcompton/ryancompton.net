// Sanity checks on a built site. Usage: node scripts/check-site.mjs [dist]
// Exits 1 and lists problems if the build is missing pages, has broken internal
// links, math that failed to render, or Markdown that leaked through as raw text.
import fs from 'node:fs';
import path from 'node:path';
import { htmlPages, contentHtml, textOf, linksOf } from './site.mjs';

const dist = path.resolve(process.argv[2] ?? 'dist');
const SITE = 'https://www.ryancompton.net';
const POSTS_DIR = 'src/content/posts';

// Links that were already dead before the Astro migration (files never committed).
const KNOWN_DEAD = new Set([
  '/assets/darknet-market-basket-analysis/learned_rules.tsv',
  '/assets/darknet-market-basket-analysis/products_vendors.zip',
]);

const problems = [];
const fail = (msg) => problems.push(msg);
const read = (f) => fs.readFileSync(path.join(dist, f), 'utf8');
const exists = (f) => fs.existsSync(path.join(dist, f)) && fs.statSync(path.join(dist, f)).isFile();

const pages = htmlPages(dist);
const postPages = pages.filter((p) => /^\d{4}\/\d{2}\/\d{2}\/[^/]+\.html$/.test(p));
const sources = fs.readdirSync(POSTS_DIR).filter((f) => /\.mdx?$/.test(f));

// 1. One page per post, plus the fixed pages.
if (postPages.length !== sources.length)
  fail(`expected ${sources.length} post pages (one per file in ${POSTS_DIR}), found ${postPages.length}`);
for (const f of ['index.html', 'about.html', '404.html', 'error.html', 'feed.xml', 'sitemap-index.xml'])
  if (!exists(f)) fail(`missing ${f}`);

// 2. Internal links and images resolve to files in the build.
function resolveTarget(page, raw) {
  let u = raw.trim();
  if (u.startsWith(SITE)) u = u.slice(SITE.length) || '/';
  if (!u || u.startsWith('#') || u.startsWith('//') || /^[a-z][a-z0-9+.-]*:/i.test(u)) return null;
  u = u.split('#')[0].split('?')[0];
  if (!u) return null;
  const abs = u.startsWith('/') ? u : path.posix.join('/', path.posix.dirname(page), u);
  try {
    return decodeURIComponent(abs);
  } catch {
    return abs;
  }
}
for (const page of pages) {
  const html = read(page);
  for (const link of linksOf(html)) {
    const target = resolveTarget(page, link);
    if (!target || KNOWN_DEAD.has(target)) continue;
    const file = target.endsWith('/') ? `${target}index.html` : target;
    if (!exists(file.slice(1))) fail(`${page}: broken link ${link}`);
  }
}

// 3. Post bodies: math rendered, no leftover Markdown/Liquid/kramdown syntax outside code.
const LEFTOVERS = [/\$\$/, /\{:/, /\{%/, /\{\{/, /\|\s*-{3}/, /!\[[^\]]*\]\(/, /\]\((?:\/|https?:)/];
for (const page of [...postPages, 'about.html']) {
  const body = contentHtml(read(page));
  if (body.includes('katex-error')) fail(`${page}: KaTeX failed to render some math`);
  const prose = textOf(body.replace(/<pre[\s\S]*?<\/pre>/g, ' ').replace(/<code[\s\S]*?<\/code>/g, ' '));
  for (const re of LEFTOVERS) {
    const m = prose.match(re);
    if (m) fail(`${page}: raw markup ${JSON.stringify(prose.slice(Math.max(0, m.index - 30), m.index + 40))}`);
  }
}

// 4. Every post has a lead picture on the home page.
if (exists('index.html')) {
  const empty = (read('index.html').match(/<span class="frame[^"]*"><\/span>/g) ?? []).length;
  if (empty) fail(`index.html: ${empty} post(s) without a lead picture (add \`image:\` front matter or a figure)`);
}

// 5. Feed and sitemap list every post.
const feed = exists('feed.xml') ? read('feed.xml') : '';
const sitemap = walk0('sitemap-');
function walk0(prefix) {
  return fs
    .readdirSync(dist)
    .filter((f) => f.startsWith(prefix) && f.endsWith('.xml'))
    .map((f) => read(f))
    .join('\n');
}
for (const p of postPages) {
  const url = `${SITE}/${p}`;
  if (!feed.includes(`<link>${url}</link>`)) fail(`feed.xml: missing ${url}`);
  if (!sitemap.includes(`<loc>${url}</loc>`)) fail(`sitemap: missing ${url}`);
}

if (problems.length) {
  console.error(`check-site: ${problems.length} problem(s)\n` + problems.map((p) => `  - ${p}`).join('\n'));
  process.exit(1);
}
console.log(`check-site: OK (${pages.length} pages, ${postPages.length} posts)`);
