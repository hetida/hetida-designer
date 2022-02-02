import { test, expect } from '@playwright/test';

test('basic test', async ({ page }) => {
  await page.goto('https://hetida-designer.dev.dsa-id.de/');

  await expect(page).toHaveTitle('hetida designer');

  const HEADER = page.locator('.home-header h1');
  await expect(HEADER).toHaveText('Welcome to hetida designer');
});
