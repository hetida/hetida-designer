import { test, expect } from '../fixtures/fixture';

test('Hover over component, load popover', async ({ page, hetidaDesigner }) => {
  // Arrange
  const categoryName = 'Arithmetic';
  const componentName = 'Pi';

  // Act
  await hetidaDesigner.clickComponentsInNavigation();
  await hetidaDesigner.clickCategoryInNavigation(categoryName);

  await hetidaDesigner.hoverItemInNavigation(categoryName, componentName);

  // Assert
  const popover = page.locator('hd-popover-transformation');
  await expect(popover).not.toBeEmpty();

  await hetidaDesigner.clearTest();
});
