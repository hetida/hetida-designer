import { test, expect } from '../fixtures/fixture';

test('Open context-menu via right-click on a workflow in navigation-menu', async ({
  page,
  hetidaDesigner
}) => {
  // Arrange
  const categoryName = 'Examples';
  const workflowName = 'Volatility Detection Example';
  const workflowTag = '1.0.1';

  // Act
  await hetidaDesigner.clickWorkflowsInNavigation();
  await hetidaDesigner.clickCategoryInNavigation(categoryName);
  // Open context-menu via right-click on a workflow
  await hetidaDesigner.rightClickItemInNavigation(
    `${workflowName}(${workflowTag})`
  );

  // Assert
  const countItemsContextMenu = await page
    .locator('.mat-mdc-menu-content >> button')
    .count();
  expect(countItemsContextMenu).toBeGreaterThan(0);

  await hetidaDesigner.clearTest();
});
