import rss from '@astrojs/rss';
import type { APIContext } from 'astro';
import { getPosts, SITE } from '../lib/posts';

// Feed readers can't resolve site-relative links, so make them absolute.
function absolutize(html: string, base: string): string {
  return html.replace(/\b(src|href)="\/(?!\/)/g, `$1="${base}/`);
}

export async function GET(context: APIContext) {
  const posts = await getPosts();
  return rss({
    title: SITE.title,
    description: SITE.description,
    site: context.site ?? SITE.url,
    items: posts.map((post) => ({
      title: post.data.title,
      link: post.url,
      pubDate: post.date,
      description: post.data.description || undefined,
      content: absolutize(post.rendered?.html ?? '', SITE.url),
      categories: post.data.tags,
    })),
  });
}
