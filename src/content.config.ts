import { defineCollection } from 'astro:content';
import { glob } from 'astro/loaders';
import { z } from 'astro/zod';

const posts = defineCollection({
  // Keep the Jekyll filename (YYYY-MM-DD-slug) as the id; the date and URL come from it.
  loader: glob({
    pattern: '*.{md,mdx}',
    base: './src/content/posts',
    generateId: ({ entry }) => entry.replace(/\.mdx?$/, ''),
  }),
  schema: z.object({
    title: z.string(),
    description: z.string().optional(),
    // Lead picture for the home page; defaults to the first figure in the post.
    image: z.string().optional(),
    tags: z.array(z.string()).default([]),
    category: z.string().nullish(),
    comments: z.boolean().optional(),
    redirect_from: z.array(z.string()).default([]),
  }),
});

export const collections = { posts };
