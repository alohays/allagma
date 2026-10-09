// Render a presentation SVG; no browser or study execution is involved.
import sharp from 'sharp';
import fs from 'node:fs/promises';
import { createHash } from 'node:crypto';
import { fileURLToPath } from 'node:url';
const source = new URL('../../media/source/results-poster.svg', import.meta.url);
const target = new URL('../../media/demo/results-poster.png', import.meta.url);
await sharp(await fs.readFile(source)).png().toFile(fileURLToPath(target));
const receiptPath = new URL('../../media/demo/results-poster-provenance.json', import.meta.url);
const receipt = JSON.parse(await fs.readFile(receiptPath, 'utf8'));
const bytes = await fs.readFile(target);
receipt.rendered_sha256 = createHash('sha256').update(bytes).digest('hex');
receipt.rendered_bytes = bytes.length;
receipt.rendered_dimensions = { width: 1280, height: 720 };
await fs.writeFile(receiptPath, JSON.stringify(receipt, null, 2)+'\n');
console.log('Rendered the 1280 × 720 result poster from unchanged scientific artifacts.');
