import { test, expect } from '../fixtures/fixture';

test('Open context-menu via right-click on a workflow in navigation-menu', async ({
  page,
  hetidaDesigner,
  navigation
}) => {
  // Test parameter
  const categoryName = 'Examples';
  const workflowName = 'Volatility Detection Example';

  // Run test
  await navigation.clickBtnNavigation('Workflows');
  await navigation.clickExpansionPanelNavigation(categoryName);
  // Open context-menu via right-click on a workflow
  await navigation.rightClickItemNavigation(categoryName, workflowName);

  // Check for items in context-menu
  const countItemsContextMenu = await page
    .locator('.mat-menu-content >> button')
    .count();
  expect(countItemsContextMenu).toBeGreaterThan(0);

  // Run clear
  await hetidaDesigner.clearTest();
});
