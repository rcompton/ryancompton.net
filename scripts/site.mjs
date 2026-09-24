// Helpers for inspecting a built site (dist/). No dependencies.
import fs from 'node:fs';
import path from 'node:path';

export function walk(dir, base = dir) {
  return fs.readdirSync(dir, { withFileTypes: true }).flatMap((e) => {
    const p = path.join(dir, e.name);
    return e.isDirectory() ? walk(p, base) : [path.relative(base, p).split(path.sep).join('/')];
  });
}

// Site pages: every .html file outside the copied assets/ tree.
export function htmlPages(dist) {
  return walk(dist)
    .filter((f) => f.endsWith('.html') && !f.startsWith('assets/'))
    .sort();
}

const ENTITIES = { amp: '&', lt: '<', gt: '>', quot: '"', apos: "'", nbsp: ' ', hellip: '…' };
export const decode = (s) =>
  s.replace(/&(#x?[0-9a-f]+|\w+);/gi, (m, e) =>
    e[0] === '#'
      ? String.fromCodePoint(e[1] === 'x' || e[1] === 'X' ? parseInt(e.slice(2), 16) : parseInt(e.slice(1), 10))
      : (ENTITIES[e] ?? m),
  );

// The main content of a page: <article> if present, else <main>, else <body>.
export function contentHtml(html) {
  for (const tag of ['article', 'main', 'body']) {
    const m = html.match(new RegExp(`<${tag}[\\s>][\\s\\S]*</${tag}>`, 'i'));
    if (m) return m[0];
  }
  return html;
}

// Visible text, whitespace-insensitive. KaTeX's hidden MathML copy is dropped.
export function textOf(html) {
  return decode(
    html
      .replace(/<span class="katex-mathml">[\s\S]*?<\/math><\/span>/g, ' ')
      .replace(/<(script|style|template)[^>]*>[\s\S]*?<\/\1>/gi, ' ')
      .replace(/<[^>]+>/g, ' '),
  )
    .replace(/\s+/g, ' ')
    .trim();
}

// href/src targets in a chunk of HTML.
export function linksOf(html) {
  return [...html.matchAll(/\s(?:href|src)="([^"]*)"/g)].map((m) => decode(m[1]));
}

export function countTags(html, tags) {
  return Object.fromEntries(tags.map((t) => [t, (html.match(new RegExp(`<${t}[\\s>/]`, 'gi')) ?? []).length]));
}
