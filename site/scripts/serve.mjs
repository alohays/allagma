// A foreground, loopback-only production server for previews and browser CI.
// Unlike development mode, this serves the real Pagefind index and base path.
import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';

const port = Number(process.env.PORT || 4322);
const root = path.resolve('dist');
const base = '/allagma/';
const types = { '.html': 'text/html; charset=utf-8', '.css': 'text/css', '.js': 'text/javascript', '.json': 'application/json', '.svg': 'image/svg+xml', '.png': 'image/png', '.jpg': 'image/jpeg', '.webp': 'image/webp', '.mp4': 'video/mp4', '.webm': 'video/webm', '.vtt': 'text/vtt', '.wasm': 'application/wasm', '.xml': 'application/xml', '.md': 'text/plain; charset=utf-8' };
http.createServer((req, res) => {
  let url;
  try { url = new URL(req.url, 'http://localhost'); } catch { res.writeHead(400).end(); return; }
  if (url.pathname === '/allagma') { res.writeHead(302, { location: base }).end(); return; }
  if (!url.pathname.startsWith(base)) { res.writeHead(404).end('Use /allagma/'); return; }
  let file;
  try { file = path.resolve(root, decodeURIComponent(url.pathname.slice(base.length))); } catch { res.writeHead(400).end(); return; }
  if (file !== root && !file.startsWith(root + path.sep)) { res.writeHead(403).end(); return; }
  try {
    let stat = fs.statSync(file);
    if (stat.isDirectory()) { file = path.join(file, 'index.html'); stat = fs.statSync(file); }
    const headers = { 'Content-Type': types[path.extname(file)] || 'application/octet-stream', 'Accept-Ranges': 'bytes', 'Cache-Control': 'no-cache' };
    const range = req.headers.range?.match(/^bytes=(\d+)-(\d*)$/);
    if (range) {
      const start = Number(range[1]), end = range[2] ? Number(range[2]) : stat.size - 1;
      if (start > end || end >= stat.size) { res.writeHead(416, {'Content-Range': `bytes */${stat.size}`}).end(); return; }
      res.writeHead(206, { ...headers, 'Content-Length': end-start+1, 'Content-Range': `bytes ${start}-${end}/${stat.size}` });
      if (req.method === 'HEAD') res.end(); else fs.createReadStream(file, {start, end}).pipe(res);
    } else {
      res.writeHead(200, { ...headers, 'Content-Length': stat.size });
      if (req.method === 'HEAD') res.end(); else fs.createReadStream(file).pipe(res);
    }
  } catch { res.writeHead(404, { 'Content-Type': 'text/plain' }).end('Not found'); }
}).listen(port, '127.0.0.1', () => console.log(`Allagma production preview: http://127.0.0.1:${port}${base}`));
