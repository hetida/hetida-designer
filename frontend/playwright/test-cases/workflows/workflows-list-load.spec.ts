import { test, expect } from '@playwright/test';
import { HetidaDesigner } from '../page-objects/hetida-designer';
import { Navigation } from '../page-objects/navigation';

test('Load workflows list', async ({ page }) => {
  const hetidaDesigner = new HetidaDesigner(page);
  const navigation = new Navigation(page);

  // Run setup
  await hetidaDesigner.setupTest();

  // Run test
  await navigation.clickBtnNavigation('workflows');

  const countWorkflows = await page.locator('hd-navigation-category').count();
  expect(countWorkflows).toBeGreaterThan(0);

  // Run clear
  await hetidaDesigner.clearTest();
});
