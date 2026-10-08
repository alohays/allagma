import { chromium } from '@playwright/test';
import { pathToFileURL } from 'node:url';
import path from 'node:path';

const browser=await chromium.launch();
try {
  for(const [source,target,width,height] of [
    ['../media/social-preview.svg','../media/social-preview.png',1280,640],
    ['../media/source/demo-poster.svg','../media/demo/poster.png',1280,720],
  ]) {
    const page=await browser.newPage({viewport:{width,height},deviceScaleFactor:1});
    await page.goto(pathToFileURL(path.resolve(source)).href);
    await page.screenshot({path:target});
    await page.close();
    console.log(`Rendered ${target} at ${width}×${height}`);
  }
} finally {await browser.close();}
