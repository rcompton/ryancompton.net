// @ts-check
import { defineConfig } from 'astro/config';
import mdx from '@astrojs/mdx';
import sitemap from '@astrojs/sitemap';
import { satteri } from '@astrojs/markdown-satteri';
import { katexPlugin } from './src/lib/katex-plugin.mjs';
import { legacyAssets } from './src/lib/legacy-assets.mjs';

export default defineConfig({
  site: 'https://www.ryancompton.net',
  // Emit /about.html and /2014/05/02/slug.html to keep the URLs Jekyll used.
  build: { format: 'file' },
  trailingSlash: 'ignore',
  markdown: {
    processor: satteri({
      features: { math: { singleDollarTextMath: false } },
      mdastPlugins: [katexPlugin],
    }),
    shikiConfig: { theme: 'monokai' },
  },
  integrations: [
    mdx(),
    sitemap({
      filter: (page) => !page.endsWith('/404'),
      // Pages are emitted as .html files (build.format: 'file'); S3 has no extensionless routing.
      serialize: (item) => ({ ...item, url: item.url.replace(/(\/[^/.]+)$/, '$1.html') }),
    }),
    legacyAssets(),
  ],
});
