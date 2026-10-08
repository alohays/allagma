import fs from 'node:fs/promises';
import path from 'node:path';

const root = path.resolve('dist');
const base = '/allagma/';
const html = new Map();
async function walk(dir) {
  for (const entry of await fs.readdir(dir, { withFileTypes: true })) {
    const file = path.join(dir, entry.name);
    if (entry.isDirectory()) await walk(file);
    else if (entry.name.endsWith('.html')) html.set(file, await fs.readFile(file, 'utf8'));
  }
}
await walk(root);
const errors = [];
let count = 0;
for (const [file, body] of html) {
  const route = base + path.relative(root, file).replace(/index\.html$/, '');
  for (const [, raw] of body.matchAll(/(?:href|src|poster)="([^"]+)"/g)) {
    const target = raw.replaceAll('&amp;', '&');
    if (/^(?:https?:|mailto:|data:|tel:|javascript:)/.test(target)) continue;
    const url = new URL(target, `https://local.invalid${route}`);
    if (!url.pathname.startsWith(base)) { errors.push(`${route}: escaped base ${target}`); continue; }
    let destination = path.join(root, decodeURIComponent(url.pathname.slice(base.length)));
    try {
      if ((await fs.stat(destination)).isDirectory()) destination = path.join(destination, 'index.html');
      await fs.access(destination);
    } catch { errors.push(`${route}: missing ${target}`); continue; }
    if (url.hash && html.has(destination)) {
      const fragment = decodeURIComponent(url.hash.slice(1));
      if (!html.get(destination).includes(`id="${fragment}"`)) errors.push(`${route}: missing fragment ${target}`);
    }
    count++;
  }
}
console.log(JSON.stringify({ pages: html.size, local_links: count, errors }, null, 2));
if (errors.length) process.exitCode = 1;
