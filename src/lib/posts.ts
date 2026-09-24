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
