import { test, expect, type Page } from '@playwright/test';
import { execFileSync } from 'node:child_process';
import { readFile } from 'node:fs/promises';

async function login(page: Page, username: string) {
  await page.goto('/');
  await page.getByLabel('Username', { exact: true }).fill(username);
  await page.getByLabel('Password', { exact: true }).fill(process.env.TAGGER_E2E_PASSWORD!);
  await page.getByRole('button', { name: 'Sign in', exact: true }).click();
  await expect(page.getByRole('heading', { name: 'Private projects' })).toBeVisible();
}

test('private projects, immutable uploads, job lifecycle, access and preferences', async ({ page, browser }) => {
  await login(page, 'browser-owner');
  await page.getByLabel('Project name').fill('Browser acceptance accounts');
  await page.getByRole('button', { name: 'Create project' }).click();
  await expect(page.getByRole('heading', { name: 'Browser acceptance accounts' })).toBeVisible();
  const projectUrl = page.url();
  await page.reload();
  await expect(page.getByRole('heading', { name: 'Browser acceptance accounts' })).toBeVisible();
  await page.getByRole('link', { name: 'Skip to main content' }).focus();
  await page.keyboard.press('Enter');
  await expect(page.locator('main')).toBeFocused();
  expect(page.url()).toBe(projectUrl);

  const bytes = Buffer.from('%PDF-1.7\n% Synthetic upload; not a conversion fixture.\n');
  await page.getByLabel('Choose a PDF').setInputFiles({ name: 'synthetic.pdf', mimeType: 'application/pdf', buffer: bytes });
  await page.getByRole('button', { name: 'Store PDF', exact: true }).click();
  await expect(page.getByRole('status')).toHaveText('Source PDF stored.');
  const downloadPromise = page.waitForEvent('download');
  await page.getByRole('link', { name: 'Download original' }).click();
  const download = await downloadPromise;
  expect(await readFile((await download.path())!)).toEqual(bytes);
  await page.getByRole('button', { name: 'Verify stored copy' }).click();
  await expect(page.getByText('Waiting for worker', { exact: true })).toBeVisible();
  // Exercise the real worker handler directly. RabbitMQ transport is a separate integration gate.
  execFileSync(process.env.TAGGER_TEST_PYTHON!, ['../api/manage.py', 'shell', '-c',
    'from jobs.models import Job; from jobs.services import execute_verification; [execute_verification(j.pk) for j in Job.objects.filter(state="queued")]']);
  await expect(page.getByText('Stored copy verified', { exact: true })).toBeVisible();
  await page.getByRole('button', { name: 'Verify stored copy' }).click();
  await page.getByRole('button', { name: 'Cancel check' }).click();
  await expect(page.getByText('Cancelled', { exact: true })).toBeVisible();

  await page.getByLabel('Account username').fill('browser-viewer');
  await page.getByRole('button', { name: 'Save access' }).click();
  await expect(page.getByRole('status')).toHaveText('Project access updated.');
  const viewerContext = await browser.newContext();
  const viewer = await viewerContext.newPage();
  await login(viewer, 'browser-viewer');
  await viewer.goto(projectUrl);
  await expect(viewer.getByRole('heading', { name: 'Browser acceptance accounts' })).toBeVisible();
  await expect(viewer.getByRole('button', { name: 'Store PDF' })).toHaveCount(0);
  await expect(viewer.getByRole('link', { name: 'Download original' })).toBeVisible();
  await page.getByRole('button', { name: 'Remove browser-viewer' }).click();
  await expect(page.getByRole('button', { name: 'Remove browser-viewer' })).toHaveCount(0);
  await viewer.reload();
  await expect(viewer.getByRole('alert')).toBeVisible();
  await expect(viewer.getByRole('link', { name: 'Download original' })).toHaveCount(0);
  await viewerContext.close();

  const outsiderContext = await browser.newContext();
  const outsider = await outsiderContext.newPage();
  await login(outsider, 'browser-outsider');
  await expect(outsider.getByRole('link', { name: /Browser acceptance accounts/ })).toHaveCount(0);
  await outsider.goto(projectUrl);
  await expect(outsider.getByRole('alert')).toBeVisible();
  await outsiderContext.close();

  await page.getByText('Appearance', { exact: true }).click();
  await page.getByLabel('Theme', { exact: true }).selectOption('dark');
  await page.getByLabel('Interface text').selectOption('large');
  await page.reload();
  await expect(page.locator('html')).toHaveAttribute('data-theme', 'dark');
  await expect(page.locator('html')).toHaveAttribute('data-size', 'large');
  await page.setViewportSize({ width: 390, height: 844 });
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
  await page.getByRole('button', { name: 'Sign out' }).click();
  await expect(page.getByRole('heading', { name: 'Sign in to your workspace' })).toBeVisible();
  await page.goto(projectUrl);
  await expect(page.getByRole('heading', { name: 'Sign in to your workspace' })).toBeVisible();
});
