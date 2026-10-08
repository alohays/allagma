import { test, expect } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';

test('landing page works in both themes without horizontal overflow', async ({ page }, info) => {
  await page.goto('./');
  await expect(page.getByRole('heading', { level: 1 })).toContainText('checkable results');
  for (const theme of ['light', 'dark']) {
    await page.getByLabel('Select theme').selectOption(theme);
    await expect(page.locator('html')).toHaveAttribute('data-theme', theme);
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
    await page.screenshot({path: `test-results/${info.project.name}-${theme}-home.png`, fullPage:true});
    const result = await new AxeBuilder({page}).withTags(['wcag2a','wcag2aa','wcag21aa']).analyze();
    expect(result.violations).toEqual([]);
  }
  await page.getByRole('link', {name: 'Run your first study'}).click();
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
  const brief = page.getByRole('tab', {name:'Brief', exact:true});
  await brief.focus();
  await page.keyboard.press('ArrowRight');
  await expect(page.getByRole('tab', {name:'Results',exact:true})).toBeFocused();
  await expect(page.getByRole('tabpanel')).toContainText('+0.06510');
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
