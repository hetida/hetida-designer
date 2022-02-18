import { test, expect } from '@playwright/test';
import { HetidaDesigner } from '../page-objects/hetida-designer';
import { Navigation } from '../page-objects/navigation';

test('Load components list', async ({ page }) => {
  const hetidaDesigner = new HetidaDesigner(page);
  const navigation = new Navigation(page);

  // Run setup
  await hetidaDesigner.setupTest();

  // Run test
  await navigation.clickBtnNavigation('components');

  // Check for loaded components
  const countComponents = await page.locator('hd-navigation-category').count();
  expect(countComponents).toBeGreaterThan(0);

  // Run clear
  await hetidaDesigner.clearTest();
});
