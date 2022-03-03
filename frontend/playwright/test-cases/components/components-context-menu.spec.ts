import { test, expect } from '@playwright/test';
import { HetidaDesigner } from '../page-objects/hetida-designer';
import { Navigation } from '../page-objects/navigation';

test('Open context-menu via right-click on a component in navigation-menu', async ({
  page
}) => {
  const hetidaDesigner = new HetidaDesigner(page);
  const navigation = new Navigation(page);
  // Test parameter
  const categoryName = 'Arithmetic';
  const componentName = 'Pi';

  // Run setup
  await hetidaDesigner.setupTest();

  // Run test
  await navigation.clickBtnNavigation('Components');
  await navigation.clickExpansionPanelNavigation(categoryName);
  // Open context-menu via right-click on a component
  await navigation.rightClickItemNavigation(categoryName, componentName);

  // Check for items in context-menu
  const countItemsContextMenu = await page
    .locator('.mat-menu-content >> button')
    .count();
  expect(countItemsContextMenu).toBeGreaterThan(0);

  // Run clear
  await hetidaDesigner.clearTest();
});
