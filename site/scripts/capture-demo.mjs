// Record actual browser interaction with a fresh, bounded local CLI workflow.
// Run from site/: node scripts/capture-demo.mjs ../work/launch/capture-NNN
import { chromium } from '@playwright/test';
import { spawn } from 'node:child_process';
import fs from 'node:fs/promises';
import path from 'node:path';
import { performance } from 'node:perf_hooks';
import { createHash } from 'node:crypto';

const output = path.resolve(process.argv[2] || '../work/launch/capture');
try { await fs.access(output); throw new Error('Use a new capture directory.'); } catch (e) { if (e.code !== 'ENOENT') throw e; }
await fs.mkdir(output, { recursive: true });
const scenes = JSON.parse(await fs.readFile('../media/source/scenes.json', 'utf8'));
const sourceNames = ['media/source/scenes.json','media/source/workbench.html','tools/demo_server.py','site/scripts/capture-demo.mjs'];
async function sourceHashes() {
  return Object.fromEntries(await Promise.all(sourceNames.map(async name => [name,createHash('sha256').update(await fs.readFile(path.join('..',name))).digest('hex')])));
}
const sources = await sourceHashes();
const port = 4331;
const server = spawn('python3', ['tools/demo_server.py', '--output', path.join(output, 'execution'), '--port', String(port)], { cwd:'..', stdio:['ignore','pipe','pipe'] });
let serverOutput = '';
server.stdout.on('data', chunk => { serverOutput += chunk; });
server.stderr.on('data', chunk => { serverOutput += chunk; });
let browser;
const timeline = [];
try {
  for (let i=0; i<50; i++) {
    if (server.exitCode !== null) throw new Error(serverOutput);
    try {
      const r=await fetch(`http://127.0.0.1:${port}/state`);
      if(r.ok) {
        const state=await r.json();
        if(state.capture_root!==path.join(output,'execution')) throw new Error('Capture port belongs to another workbench.');
        break;
      }
    } catch (error) { if(error.message?.includes('another workbench')) throw error; }
    await new Promise(r=>setTimeout(r,100));
  }
  browser = await chromium.launch();
  const context = await browser.newContext({viewport:{width:1600,height:900}, deviceScaleFactor:1,
    recordVideo:{dir:path.join(output,'raw'),size:{width:1600,height:900}}, reducedMotion:'reduce'});
  const page = await context.newPage();
  const video = page.video();
  const begun = performance.now();
  await page.goto(`http://127.0.0.1:${port}/`);
  await page.getByRole('heading', {name:'Does adding a bias increase squared error?'}).waitFor();
  for (const scene of scenes.scenes) {
    if (scene.id !== 'brief' && scene.id !== 'audit') await page.locator(`[data-chapter="${scene.id}"]`).click();
    const start = (performance.now()-begun)/1000;
    if (scene.id === 'execute') {
      await page.getByRole('button',{name:'Run the offline study',exact:true}).click();
      await page.getByText('Complete. All 28 attempts retained; 24 confirmation seeds analyzed.',{exact:true}).waitFor({timeout:110000});
    }
    if (scene.id === 'audit') {
      await page.getByRole('button',{name:'Recompute & audit',exact:true}).click();
      await page.getByText('PASS · 521 references',{exact:true}).waitFor({timeout:30000});
    }
    const remaining=scene.seconds*1000-(performance.now()-begun-start*1000);
    if(remaining>0) await page.waitForTimeout(remaining);
    const end=(performance.now()-begun)/1000;
    timeline.push({...scene,start,end});
    await page.screenshot({path:path.join(output,`${scene.id}.png`)});
    console.log(`${scene.id}: ${(end-start).toFixed(2)} seconds`);
  }
  const finalState=await (await fetch(`http://127.0.0.1:${port}/state`)).json();
  if(finalState.audit?.verdict!=='pass'||finalState.counts.succeeded!==26) throw new Error('Actual study did not pass.');
  await fs.writeFile(path.join(output,'state.json'), JSON.stringify(finalState,null,2)+'\n');
  await context.close();
  const raw=await video.path();
  if(JSON.stringify(sources)!==JSON.stringify(await sourceHashes())) throw new Error('Capture source changed while recording.');
  await fs.writeFile(path.join(output,'timeline.json'), JSON.stringify({format:'allagma-video-capture-v1',raw:path.relative(output,raw),viewport:{width:1600,height:900},scope:scenes.scope,source_files:sources,scenes:timeline},null,2)+'\n');
  console.log(`Capture saved to ${output}`);
} finally {
  if(browser) await browser.close();
  server.kill('SIGTERM');
  await fs.writeFile(path.join(output,'server.log'),serverOutput);
}
