import { test, expect } from '@playwright/test';
import { HetidaDesigner } from '../page-objects/hetida-designer';
import { Navigation } from '../page-objects/navigation';

test('Click on home tab', async ({ page }) => {
  const hetidaDesigner = new HetidaDesigner(page);
  const naviagtion = new Navigation(page);

  // Run setup
  await hetidaDesigner.setupTest();

  // Run test
  await naviagtion.clickTabNavigation(0);

  const homeHeader = page.locator('.home-header h1');
  await expect(homeHeader).toHaveText('Welcome to hetida designer');

  // Run clear
  await hetidaDesigner.clearTest();
});
