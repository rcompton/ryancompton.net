Source for [ryancompton.net](https://www.ryancompton.net), built with [Astro](https://astro.build).

## Develop

Requires Node 22.12+ (see `.nvmrc`).

```sh
npm install
npm run dev      # http://localhost:4321
npm run build    # writes the site to dist/
npm run preview  # serves dist/
npm test         # build + sanity checks (broken links, missing pages, unrendered math/Markdown)
```

Pushing to `master` builds the site, runs the sanity checks, and deploys to S3/CloudFront
(`.github/workflows/build_and_deploy.yml`).

## Dependency updates

Dependabot opens one grouped npm PR per week (majors separately). The PR check
(`.github/workflows/pr_check.yml`) builds both the PR and `master` and compares every page's
text, links and images (`scripts/compare-builds.mjs`). A Dependabot PR must render the site
identically; minor/patch npm and GitHub Actions updates that pass are merged and deployed
automatically. Major updates wait for review. To compare two builds locally:

```sh
node scripts/compare-builds.mjs path/to/old/dist dist
```

## Writing a post

Add `src/content/posts/YYYY-MM-DD-slug.md`:

```md
---
title: "Post title"
tags: ["coding"]
image: "/assets/leads/post-title.png"   # optional
---

Intro paragraph shown on the home page.

<!--more-->

Rest of the post.
```

- The URL is `/YYYY/MM/DD/slug.html`, taken from the filename.
- Every post needs a lead picture for the home page: `image:` in front matter, or else the first figure/YouTube video in the post is used. `npm test` fails if a post has none.
- Math: `$$x^2$$` inline, or `$$` on its own lines for display math (rendered with KaTeX at build time).
- Use `.mdx` instead of `.md` to embed Astro/JS components in a post.
- Files under `assets/` are published at `/assets/...`; link them as `/assets/pix/foo.png`.
- `redirect_from:` lists old directory-style URLs (`/2014/12/23/hearddit/`) that should redirect to the post.

## Layout

- `src/content/posts/` – posts (Markdown)
- `src/pages/` – home, about, 404, RSS feed (`/feed.xml`), post and redirect routes
- `src/layouts/`, `src/styles/global.css` – page chrome and the whole theme (plain CSS, no web fonts)
- `assets/` – images, data, notebooks and code referenced by posts. Kept at the repo root because the padmapper job (`assets/padmapper/padmapper_charts.py`) writes into it.
- `public/` – favicons, web manifest and other files served as-is

## License

[MIT](http://opensource.org/licenses/MIT)
