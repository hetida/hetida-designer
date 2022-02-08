import { test, expect } from '@playwright/test';
import { HetidaDesignerDevPage } from '../page-objects/hetida-designer-dev-page';

test('workflows list is loading', async ({ page }) => {
  // Run setup
  let hetidaDesignerDevPage = new HetidaDesignerDevPage(page);
  await hetidaDesignerDevPage.setupTest();

  // Run test
  await page.locator('button:has-text("workflows")').click();
  await page.waitForSelector('hd-navigation-category'); // Waiting for the workflows list to finsh loading

  expect(await page.locator('hd-navigation-category').count()).toBeGreaterThan(0);

  // Run clear
  await hetidaDesignerDevPage.clearTest();
});
