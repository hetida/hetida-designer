import { test, expect } from '../fixtures/fixture';

test('Open context-menu via right-click on a component in navigation-menu', async ({
  page,
  hetidaDesigner
}) => {
  // Arrange
  const categoryName = 'Arithmetic';
  const componentName = 'Pi';

  // Act
  await hetidaDesigner.clickComponentsInNavigation();
  await hetidaDesigner.clickCategoryInNavigation(categoryName);
  // Open context-menu via right-click on a component
  await hetidaDesigner.rightClickItemInNavigation(categoryName, componentName);

  // Assert
  const countItemsContextMenu = await page
    .locator('.mat-mdc-menu-content >> button')
    .count();
  expect(countItemsContextMenu).toBeGreaterThan(0);

  await hetidaDesigner.clearTest();
});
