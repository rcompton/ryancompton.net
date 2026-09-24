import { getPosts, SITE } from './posts';

// Old URLs listed in each post's `redirect_from` front matter.
export async function getRedirects(): Promise<{ from: string; to: string }[]> {
  const posts = await getPosts();
  return posts.flatMap((post) => post.data.redirect_from.map((from) => ({ from, to: new URL(post.url, SITE.url).href })));
}

// Old directory-style URLs (/2014/12/23/hearddit/) get a redirect page at .../index.html.
export function redirectFile(from: string): string | null {
  return from.endsWith('/') ? `${from}index.html` : null;
}

export function redirectPage(to: string): string {
  return `<!DOCTYPE html>
<html lang="en-US">
  <meta charset="utf-8">
  <title>Redirecting&hellip;</title>
  <link rel="canonical" href="${to}">
  <script>location="${to}"</script>
  <meta http-equiv="refresh" content="0; url=${to}">
  <meta name="robots" content="noindex">
  <h1>Redirecting&hellip;</h1>
  <a href="${to}">Click here if you are not redirected.</a>
</html>
`;
}
