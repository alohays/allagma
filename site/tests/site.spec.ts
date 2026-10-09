import { test, expect } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';
import { readFileSync } from 'node:fs';
import { createHash } from 'node:crypto';

test('opening shows a playable result and direct routes to a study and its report', async ({ page }) => {
  await page.goto('./');
  const hero = page.locator('.launch-hero');
  const play = hero.getByRole('button', {name:'Play demo 1:40'});
  // At the tested phone and desktop sizes, the play control is in the opening viewport.
  await expect(play).toBeInViewport({ ratio: 1 });
  await play.focus();
  await page.keyboard.press('Enter');
  const video = hero.locator('video');
  await expect.poll(() => video.evaluate((v:HTMLVideoElement) => v.currentTime)).toBeGreaterThan(.3);
  await expect(play).toBeHidden();
  await video.evaluate((v:HTMLVideoElement) => v.pause());
  await hero.getByRole('link',{name:'Read the report excerpt',exact:true}).click();
  await expect(page.getByRole('tab',{name:'Report',exact:true})).toHaveAttribute('aria-selected','true');
  await expect(page.getByRole('tabpanel').locator('blockquote')).toContainText('24');
  await page.reload();
  await expect(page.getByRole('tab',{name:'Report',exact:true})).toHaveAttribute('aria-selected','true');
  await page.goto('./');
  await hero.getByRole('link',{name:'Read a completed study',exact:true}).click();
  await expect(page).toHaveURL(/studies\/ema-schedule\/$/);
  await expect(page.locator('main')).toContainText('The result below is retained work from run r07');
});

test('media and report downloads retain their source bytes', async ({page}) => {
  for (const [route, name, source] of [
    ['demo/', 'Download MP4 (2.9 MB)', '../media/demo/allagma-workflow.mp4'],
    ['demo/', 'Download English captions', '../media/demo/allagma-workflow.en.vtt'],
    ['explore/#panel-report', 'Download the full generated manuscript (Markdown)', '../media/evidence/toy-manuscript.md'],
    ['./', "Download the agent's full report (Markdown)", '../media/evidence/ema-r07-report.md'],
  ]) {
    await page.goto(route);
    const ready = page.waitForEvent('download');
    await page.getByRole('link',{name}).click();
    const download = await ready;
    const actual = readFileSync((await download.path())!);
    expect(createHash('sha256').update(actual).digest('hex')).toBe(createHash('sha256').update(readFileSync(source)).digest('hex'));
  }
});

test('landing page works in both themes without horizontal overflow', async ({ page }, info) => {
  await page.goto('./');
  await expect(page.getByRole('heading', { level: 1 })).toContainText('carry out a study');
  for (const theme of ['light', 'dark']) {
    await page.getByLabel('Select theme').selectOption(theme);
    await expect(page.locator('html')).toHaveAttribute('data-theme', theme);
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
    await page.screenshot({path: `test-results/${info.project.name}-${theme}-home.png`, fullPage:true});
    const result = await new AxeBuilder({page}).withTags(['wcag2a','wcag2aa','wcag21aa']).analyze();
    expect(result.violations).toEqual([]);
  }
  await page.getByRole('link', {name: 'Try the offline example'}).click();
  await expect(page).toHaveURL(/\/allagma\/guides\/first-study\/$/);
  await expect(page.getByRole('heading', { level: 1 })).toHaveText('Your first study');
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
});

test('production search finds the tutorial and navigates under the base path', async ({ page }) => {
  await page.goto('./');
  await page.getByRole('button', {name: 'Search', exact: true}).click();
  const search = page.getByRole('textbox', {name:'Search', exact:true});
  await search.fill('confirmation seeds');
  const result = page.locator('.pagefind-ui__result-link').filter({ hasText: /first study|Read the result|experiment/i }).first();
  await expect(result).toBeVisible();
  await result.click();
  await expect(page).toHaveURL(/\/allagma\//);
  await expect(page.getByRole('heading', { level: 1 })).toHaveText('Your first study');
});

test('artifact tabs support keyboard navigation and show actual values', async ({ page }, info) => {
  await page.goto('explore/');
  const resultsTab = page.getByRole('tab', {name:'Results', exact:true});
  await expect(resultsTab).toHaveAttribute('aria-selected','true');
  await expect(page.getByRole('tabpanel')).toContainText('+0.06510');
  await resultsTab.focus();
  await page.keyboard.press('ArrowRight');
  await expect(page.getByRole('tab', {name:'Report',exact:true})).toBeFocused();
  await expect(page.getByRole('tabpanel').locator('blockquote')).toContainText('sample mean plus 0.25');
  await page.keyboard.press('ArrowRight');
  await expect(page.getByRole('tab', {name:'Claims',exact:true})).toBeFocused();
  await expect(page.getByRole('tabpanel')).toContainText('contradicted');
  await page.getByRole('tabpanel').getByText('Evidence scope and references', {exact:true}).first().click();
  await expect(page.getByRole('tabpanel')).toContainText('24 prespecified seeds');
  await page.screenshot({path:`test-results/${info.project.name}-claims.png`, fullPage:true});
  const results = await new AxeBuilder({page}).withTags(['wcag2a','wcag2aa','wcag21aa']).analyze();
  expect(results.violations).toEqual([]);
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
});

test('study pages load figures and retain their scientific limits', async ({ page }) => {
  await page.goto('studies/ema-schedule/');
  await expect(page.getByRole('heading', {level:1})).toHaveText('Weight EMA');
  const figure = page.getByAltText('Paired EMA effects by duration and policy');
  await expect(figure).toBeVisible();
  expect(await figure.evaluate((img:HTMLImageElement) => img.complete && img.naturalWidth > 0)).toBe(true);
  await expect(page.locator('main')).toContainText('independent scientific peer review');
  await page.goto('studies/modular-addition/');
  await expect(page.locator('main')).toContainText('None reached 95%');
  await page.goto('studies/core-culp/');
  await expect(page.locator('main')).toContainText('label defect');
});

test('skip link and mobile menu are usable', async ({page}, info) => {
  await page.goto('guides/first-study/');
  await page.keyboard.press('Tab');
  await expect(page.getByRole('link', {name:'Skip to content'})).toBeFocused();
  await page.keyboard.press('Enter');
  await expect(page).toHaveURL(/#_top$/);
  if (info.project.name === 'mobile') {
    await page.getByRole('button', {name:'Menu', exact:true}).click();
    await expect(page.getByRole('link', {name:'Start a native study',exact:true})).toBeVisible();
    await page.getByRole('link', {name:'Start a native study',exact:true}).click();
    await expect(page).toHaveURL(/guides\/native-study\/$/);
  }
});

test('flagship video decodes, plays, seeks and loads English captions', async ({page}, info) => {
  await page.goto('demo/');
  const video = page.locator('video');
  await expect(video).toHaveAttribute('preload','metadata');
  await video.evaluate(async (v:HTMLVideoElement) => { v.muted=true; await v.play(); });
  await expect.poll(() => video.evaluate((v:HTMLVideoElement) => v.currentTime)).toBeGreaterThan(.5);
  const decoded = await video.evaluate((v:HTMLVideoElement) => ({duration:v.duration,width:v.videoWidth,height:v.videoHeight,error:v.error?.code||null,tracks:v.textTracks.length}));
  expect(decoded.duration).toBeGreaterThanOrEqual(60);
  expect(decoded.duration).toBeLessThanOrEqual(120);
  expect(decoded.width).toBe(1600);
  expect(decoded.height).toBe(900);
  expect(decoded.error).toBeNull();
  expect(decoded.tracks).toBe(1);
  await expect.poll(() => video.evaluate((v:HTMLVideoElement) => v.textTracks[0]?.cues?.length||0)).toBeGreaterThan(10);
  await video.evaluate((v:HTMLVideoElement) => { v.currentTime=85; });
  await expect.poll(() => video.evaluate((v:HTMLVideoElement) => v.currentTime)).toBeGreaterThan(85);
  await page.screenshot({path:`test-results/${info.project.name}-video.png`});
  await video.evaluate((v:HTMLVideoElement) => v.pause());
  await page.getByRole('link',{name:'Read the transcript',exact:true}).click();
  await expect(page.getByRole('heading',{level:1})).toHaveText('Video transcript');
});

test('every canonical page renders inside the viewport with no script errors', async ({page}) => {
  const pages: {route:string}[] = JSON.parse(readFileSync('content-map.json','utf8'));
  const errors:string[]=[];
  page.on('pageerror', error=>errors.push(error.message));
  for (const entry of pages) {
    const response=await page.goto(entry.route+'/');
    expect(response?.status(), entry.route).toBe(200);
    await expect(page.getByRole('heading',{level:1})).toBeVisible();
    expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),entry.route).toBe(true);
  }
  expect(errors).toEqual([]);
});
