// Compare two builds of the site page by page.
// Usage: node scripts/compare-builds.mjs <base-dist> <head-dist> [--strict]
//
// For a dependency-only change (e.g. a Dependabot PR) the rendered site should be
// identical: same pages, same text, same links and images. With --strict any
// difference exits 1. A Markdown report is printed (and appended to the GitHub
// Actions job summary when running in CI).
import fs from 'node:fs';
import path from 'node:path';
import { htmlPages, contentHtml, textOf, linksOf, countTags } from './site.mjs';

const [baseDir, headDir] = process.argv.slice(2).filter((a) => !a.startsWith('--')).map((d) => path.resolve(d));
const strict = process.argv.includes('--strict');
if (!baseDir || !headDir) {
  console.error('usage: node scripts/compare-builds.mjs <base-dist> <head-dist> [--strict]');
  process.exit(2);
}

const TAGS = ['a', 'img', 'iframe', 'audio', 'video', 'table', 'pre', 'h1', 'h2', 'h3', 'li'];
const snapshot = (dir, page) => {
  const html = contentHtml(fs.readFileSync(path.join(dir, page), 'utf8'));
  return { text: textOf(html), links: linksOf(html).sort(), counts: countTags(html, TAGS) };
};

function firstDifference(a, b) {
  let i = 0;
  while (i < a.length && i < b.length && a[i] === b[i]) i++;
  const from = Math.max(0, i - 40);
  return { before: a.slice(from, i + 60), after: b.slice(from, i + 60) };
}

const basePages = new Set(htmlPages(baseDir));
const headPages = new Set(htmlPages(headDir));
const removed = [...basePages].filter((p) => !headPages.has(p));
const added = [...headPages].filter((p) => !basePages.has(p));
const changed = [];

for (const page of [...basePages].filter((p) => headPages.has(p))) {
  const a = snapshot(baseDir, page);
  const b = snapshot(headDir, page);
  const notes = [];
  if (a.text !== b.text) {
    const d = firstDifference(a.text, b.text);
    notes.push(`text differs:\n  - before: \`${d.before}\`\n  - after:  \`${d.after}\``);
  }
  const lostLinks = a.links.filter((l) => !b.links.includes(l));
  const newLinks = b.links.filter((l) => !a.links.includes(l));
  if (lostLinks.length) notes.push(`links removed: ${lostLinks.slice(0, 5).map((l) => `\`${l}\``).join(', ')}`);
  if (newLinks.length) notes.push(`links added: ${newLinks.slice(0, 5).map((l) => `\`${l}\``).join(', ')}`);
  const counts = TAGS.filter((t) => a.counts[t] !== b.counts[t]).map((t) => `${t} ${a.counts[t]}→${b.counts[t]}`);
  if (counts.length) notes.push(`element counts: ${counts.join(', ')}`);
  if (notes.length) changed.push({ page, notes });
}

const identical = !removed.length && !added.length && !changed.length;
let report = `## Rendered site comparison\n\n`;
report += identical
  ? `No differences across ${headPages.size} pages.\n`
  : `${removed.length} removed, ${added.length} added, ${changed.length} changed (of ${basePages.size} pages).\n`;
if (removed.length) report += `\n### Removed pages\n${removed.map((p) => `- \`/${p}\``).join('\n')}\n`;
if (added.length) report += `\n### Added pages\n${added.map((p) => `- \`/${p}\``).join('\n')}\n`;
if (changed.length)
  report += `\n### Changed pages\n${changed.map((c) => `- \`/${c.page}\`\n${c.notes.map((n) => `  - ${n}`).join('\n')}`).join('\n')}\n`;

console.log(report);
if (process.env.GITHUB_STEP_SUMMARY) fs.appendFileSync(process.env.GITHUB_STEP_SUMMARY, report + '\n');
process.exit(strict && !identical ? 1 : 0);
