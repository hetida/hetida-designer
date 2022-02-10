import { test, expect } from '@playwright/test';
import { HetidaDesigner } from '../page-objects/hetida-designer';

test('Load landingpage', async ({ page }) => {
  const hetidaDesigner = new HetidaDesigner(page);

  // Run setup
  await hetidaDesigner.setupTest();

  // Run test
  await expect(page).toHaveTitle('hetida designer');

  const homeHeader = page.locator('.home-header h1');
  await expect(homeHeader).toHaveText('Welcome to hetida designer');

  // Run clear
  await hetidaDesigner.clearTest();
});
