import { getCollection, type CollectionEntry } from 'astro:content';

export const SITE = {
  title: 'Ryan Compton',
  description: 'Ryan Compton personal blog.',
  email: 'ryan@ryancompton.net',
  url: 'https://www.ryancompton.net',
};

export type Post = CollectionEntry<'posts'> & {
  date: Date;
  year: string;
  month: string;
  day: string;
  slug: string;
  url: string;
};

// Jekyll's "pretty" slugify, which produced the existing post URLs.
function slugify(s: string): string {
  return s
    .toLowerCase()
    .replace(/[^a-z0-9._~!$&'()+,;=@]+/g, '-')
    .replace(/-{2,}/g, '-')
    .replace(/^-|-$/g, '');
}

export function withMeta(entry: CollectionEntry<'posts'>): Post {
  const m = entry.id.match(/^(\d{4})-(\d{2})-(\d{2})-(.+)$/);
  if (!m) throw new Error(`Post filename must start with YYYY-MM-DD-: ${entry.id}`);
  const [, year, month, day, rest] = m;
  const slug = slugify(rest);
  return {
    ...entry,
    date: new Date(`${year}-${month}-${day}T00:00:00Z`),
    year,
    month,
    day,
    slug,
    url: `/${year}/${month}/${day}/${slug}.html`,
  };
}

export async function getPosts(): Promise<Post[]> {
  const entries = await getCollection('posts');
  return entries.map(withMeta).sort((a, b) => b.date.getTime() - a.date.getTime() || b.id.localeCompare(a.id));
}

export function formatDate(d: Date): string {
  return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric', timeZone: 'UTC' });
}

// Content before <!--more-->, or the whole post if there is no marker (Jekyll's behavior).
export function excerptHtml(html: string): string {
  const i = html.indexOf('<!--more-->');
  return i === -1 ? html : html.slice(0, i);
}

const ENTITIES: Record<string, string> = { amp: '&', lt: '<', gt: '>', quot: '"', apos: "'", nbsp: ' ' };
const decode = (s: string) =>
  s.replace(/&(#x?[0-9a-f]+|\w+);/gi, (m, e: string) =>
    e[0] === '#'
      ? String.fromCodePoint(e[1].toLowerCase() === 'x' ? parseInt(e.slice(2), 16) : parseInt(e.slice(1), 10))
      : (ENTITIES[e] ?? m),
  );

// A short plain-text preview for the home page: the opening prose paragraphs of the
// excerpt, skipping paragraphs that are only media, contain math, or are an italic
// note such as "Originally published at ...".
export function previewText(html: string, max = 240): string {
  let text = '';
  for (const [, inner] of excerptHtml(html).matchAll(/<p>([\s\S]*?)<\/p>/g)) {
    if (inner.includes('katex') || /^\s*<em>[\s\S]*<\/em>\s*$/.test(inner)) continue;
    const t = decode(inner.replace(/<[^>]+>/g, '')).replace(/\s+/g, ' ').trim();
    if (!t) continue;
    text = text ? `${text} ${t}` : t;
    if (text.length >= 140) break;
  }
  if (text.length <= max) return text;
  return text.slice(0, text.lastIndexOf(' ', max)).replace(/[\s,;:.–—-]+$/, '') + '…';
}
