import { test, expect } from '@playwright/test';
import { HetidaDesignerDevPage } from '../page-objects/hetida-designer-dev-page';

test('workflows are executing', async ({ page }) => {
  // Run setup
  let hetidaDesignerDevPage = new HetidaDesignerDevPage(page);
  await hetidaDesignerDevPage.setupTest();

  // Run test
  await page.locator('button:has-text("workflows")').click();
  await page.waitForSelector('hd-navigation-category'); // Waiting for the workflows-list to finsh loading

  // Expansion-panel is expanding
  await page.locator('hd-navigation-category').first().locator('.mat-expansion-panel-header').click();

  // Workflow is opening on double-click and loading
  await page.locator('hd-navigation-category').first().locator('.expansion-panel-content').first()
    .locator('.navigation-item').dblclick();

  // Executing workflow
  //await expect();

  // Run clear
  await hetidaDesignerDevPage.clearTest();
});
