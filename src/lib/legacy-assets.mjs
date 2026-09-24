// Serve and publish the top-level assets/ directory at /assets/.
//
// assets/ stays at the repo root (not public/) because the padmapper cron job
// writes into ~/ryancompton.net/assets/ and commits from there.
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const SRC = path.resolve('assets');
// Match Jekyll, which never published dotfiles or names starting with _.
const skip = (p) => /^[._]/.test(path.basename(p));

const MIME = {
  '.html': 'text/html', '.css': 'text/css', '.js': 'text/javascript', '.json': 'application/json',
  '.png': 'image/png', '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.gif': 'image/gif',
  '.svg': 'image/svg+xml', '.pdf': 'application/pdf', '.wav': 'audio/wav', '.txt': 'text/plain',
  '.tsv': 'text/tab-separated-values', '.csv': 'text/csv', '.xml': 'application/xml',
};

export function legacyAssets() {
  return {
    name: 'legacy-assets',
    hooks: {
      'astro:server:setup': ({ server }) => {
        server.middlewares.use((req, res, next) => {
          const url = decodeURIComponent((req.url ?? '').split('?')[0]);
          if (!url.startsWith('/assets/')) return next();
          const file = path.join(SRC, url.slice('/assets/'.length));
          if (!file.startsWith(SRC) || !fs.existsSync(file) || !fs.statSync(file).isFile()) return next();
          res.setHeader('Content-Type', MIME[path.extname(file).toLowerCase()] ?? 'application/octet-stream');
          fs.createReadStream(file).pipe(res);
        });
      },
      'astro:build:done': ({ dir }) => {
        const dest = path.join(fileURLToPath(dir), 'assets');
        fs.cpSync(SRC, dest, { recursive: true, filter: (p) => !skip(p) });
      },
    },
  };
}
