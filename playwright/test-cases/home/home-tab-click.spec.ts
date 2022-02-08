import { test, expect } from '@playwright/test';
import { HetidaDesignerDevPage } from '../page-objects/hetida-designer-dev-page';

test('clicking on home tab', async ({ page }) => {
  // Run setup
  let hetidaDesignerDevPage = new HetidaDesignerDevPage(page);
  await hetidaDesignerDevPage.setupTest();

  // Run test
  await page.locator('div[role="tab"] >> nth=0').click();

  await expect(page.locator('.home-header h1')).toHaveText('Welcome to hetida designer');

  // Run clear
  await hetidaDesignerDevPage.clearTest();
});
