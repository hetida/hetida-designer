import { test, expect } from '../fixtures/fixture';

test('Open context-menu via right-click on a component in navigation-menu', async ({
  page,
  hetidaDesigner,
  navigation
}) => {
  // Test parameter
  const categoryName = 'Arithmetic';
  const componentName = 'Pi';

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
