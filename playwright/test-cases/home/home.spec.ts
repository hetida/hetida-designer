import { test } from '@playwright/test';
import { HetidaDesignerDevPage } from '../page-objects/hetida-designer-dev-page';

test('home', async ({ page }) => {
  // Run setup, test home
  let hetidaDesignerDevPage = new HetidaDesignerDevPage(page);
  await hetidaDesignerDevPage.setup();
});
