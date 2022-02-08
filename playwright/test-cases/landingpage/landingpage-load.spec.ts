import { test, expect } from '@playwright/test';
import { HetidaDesignerDevPage } from '../page-objects/hetida-designer-dev-page';

test('landingpage is loading', async ({ page }) => {
  // Run setup
  let hetidaDesignerDevPage = new HetidaDesignerDevPage(page);
  await hetidaDesignerDevPage.setupTest();

  // Run test
  await expect(page).toHaveTitle('hetida designer');
  await expect(page.locator('.home-header h1')).toHaveText('Welcome to hetida designer');

  // Run clear
  await hetidaDesignerDevPage.clearTest();
});
