import type { APIRoute, GetStaticPaths } from 'astro';
import { getRedirects, redirectFile, redirectPage } from '../lib/redirects';

export const getStaticPaths = (async () => {
  const redirects = await getRedirects();
  return redirects.flatMap(({ from, to }) => {
    const file = redirectFile(from);
    return file ? [{ params: { redirect: file.replace(/^\//, '') }, props: { to } }] : [];
  });
}) satisfies GetStaticPaths;

export const GET: APIRoute = ({ props }) =>
  new Response(redirectPage(props.to), { headers: { 'Content-Type': 'text/html; charset=utf-8' } });
