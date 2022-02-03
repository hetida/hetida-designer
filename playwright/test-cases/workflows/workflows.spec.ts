import { test, expect } from '@playwright/test';
import { HetidaDesignerDevPage } from '../page-objects/hetida-designer-dev-page';

test('workflows', async ({ page }) => {
  // Run setup
  let hetidaDesignerDevPage = new HetidaDesignerDevPage(page);
  await hetidaDesignerDevPage.setup();

  // Run test workflows
  await page.locator('').click();
});
