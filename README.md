Source for [ryancompton.net](https://www.ryancompton.net), built with [Astro](https://astro.build).

## Develop

Requires Node 22.12+ (see `.nvmrc`).

```sh
npm install
npm run dev      # http://localhost:4321
npm run build    # writes the site to dist/
npm run preview  # serves dist/
```

Pushing to `master` builds the site and deploys it to S3/CloudFront (`.github/workflows/build_and_deploy.yml`).

## Writing a post

Add `src/content/posts/YYYY-MM-DD-slug.md`:

```md
---
title: "Post title"
tags: ["coding"]
---

Intro paragraph shown on the home page.

<!--more-->

Rest of the post.
```

- The URL is `/YYYY/MM/DD/slug.html`, taken from the filename.
- Everything before `<!--more-->` is the excerpt on the home page (the whole post if there is no marker).
- Math: `$$x^2$$` inline, or `$$` on its own lines for display math (rendered with KaTeX at build time).
- Use `.mdx` instead of `.md` to embed Astro/JS components in a post.
- Files under `assets/` are published at `/assets/...`; link them as `/assets/pix/foo.png`.
- `redirect_from:` lists old directory-style URLs (`/2014/12/23/hearddit/`) that should redirect to the post.

## Layout

- `src/content/posts/` – posts (Markdown)
- `src/pages/` – home, about, 404, RSS feed (`/feed.xml`), post and redirect routes
- `src/layouts/`, `src/styles/` – page chrome; `minima.css` is the compiled dark skin of the old Jekyll theme
- `assets/` – images, data, notebooks and code referenced by posts. Kept at the repo root because the padmapper job (`assets/padmapper/padmapper_charts.py`) writes into it.
- `public/` – favicons, web manifest and other files served as-is

## License

[MIT](http://opensource.org/licenses/MIT)
