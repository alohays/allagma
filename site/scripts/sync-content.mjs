import fs from 'node:fs/promises';
import { existsSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { execFileSync } from 'node:child_process';
import { writeVendorNotices } from './vendor-notices.mjs';

const site = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const root = path.dirname(site);
const pages = JSON.parse(await fs.readFile(path.join(site, 'content-map.json'), 'utf8'));
const routes = new Map(pages.map(p => [p.source, `/allagma/${p.route}/`]));
const generated = path.join(site, 'src/content/docs/generated');
const assets = path.join(site, 'public/generated');
await fs.rm(generated, { recursive: true, force: true });
await fs.rm(assets, { recursive: true, force: true });
await fs.mkdir(generated, { recursive: true });
await fs.mkdir(assets, { recursive: true });
const receipts = [];
const verifiedTargets = new Set();

async function rewrite(body, source) {
  const links = [...body.matchAll(/(!?)\[([^\]]*)\]\(([^\s)]+)(?:\s+"[^"]*")?\)/g)];
  for (const match of links.reverse()) {
    const [, image, label, target] = match;
    if (/^(https?:|mailto:|#|\/)/.test(target)) continue;
    const [file, fragment] = target.split('#');
    const resolved = path.posix.normalize(path.posix.join(path.posix.dirname(source), decodeURI(file)));
    if (resolved.startsWith('../')) throw new Error(`Link escapes repository: ${source}: ${target}`);
    if (!existsSync(path.join(root, resolved)) && !verifiedTargets.has(resolved)) {
      execFileSync('git', ['ls-files', '--error-unmatch', '--', resolved], { cwd: root, stdio: 'pipe' });
      verifiedTargets.add(resolved);
    }
    let href;
    if (image) {
      const destination = path.join(assets, resolved);
      await fs.mkdir(path.dirname(destination), { recursive: true });
      await fs.copyFile(path.join(root, resolved), destination);
      href = `/allagma/generated/${resolved}`;
    } else {
      href = routes.get(resolved) || `https://github.com/alohays/allagma/blob/main/${resolved}`;
    }
    if (fragment) href += '#' + fragment;
    body = body.slice(0, match.index) + `${image}[${label}](${href})` + body.slice(match.index + match[0].length);
  }
  return body;
}

for (const page of pages) {
  const body = await rewrite((await fs.readFile(path.join(root, page.source), 'utf8')).replace(/^# .+\n+/, ''), page.source);
  const destination = path.join(generated, page.route + '.md');
  await fs.mkdir(path.dirname(destination), { recursive: true });
  const front = `---\ntitle: ${JSON.stringify(page.title)}\nslug: ${page.route}\neditUrl: https://github.com/alohays/allagma/edit/main/${page.source}\n---\n\n`;
  await fs.writeFile(destination, front + body + `\n\n---\n\n[Canonical source](https://github.com/alohays/allagma/blob/main/${page.source}) · Generated from the maintained repository document.\n`);
  receipts.push(page);
}

const help = execFileSync('python3', ['tools/cli_reference.py'], { cwd: root, encoding: 'utf8' });
await fs.mkdir(path.join(generated, 'reference'), { recursive: true });
await fs.writeFile(path.join(generated, 'reference/commands.md'), '---\ntitle: All command flags\nslug: reference/commands\n---\n\n' + help);
const mediaRoot = path.join(root, 'media');
await fs.cp(mediaRoot, path.join(assets, 'media'), {
  recursive: true,
  // Editable capture sources live in Git. The workbench requires its local
  // Python server and must never masquerade as a working static-site feature.
  filter: file => path.relative(mediaRoot, file).split(path.sep)[0] !== 'source',
});
await fs.writeFile(path.join(assets, 'content-sources.json'), JSON.stringify(receipts, null, 2) + '\n');
await writeVendorNotices(site,path.join(assets,'third-party-licenses.txt'));
console.log(`Synced ${pages.length} canonical pages, command help, and selected media.`);
