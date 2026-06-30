import { test, expect } from '../fixtures/fixture';

test('Hover over component, load popover', async ({ page, hetidaDesigner }) => {
  // Arrange
  const categoryName = 'Arithmetic';
  const componentName = 'Pi';
  const componentTag = '1.0.0';

  // Act
  await hetidaDesigner.clickComponentsInNavigation();
  await hetidaDesigner.clickCategoryInNavigation(categoryName);

  await hetidaDesigner.hoverItemInNavigation(
    `${componentName}(${componentTag})`
  );

  // Assert
  const popover = page.locator('hd-popover-transformation');
  await expect(popover).not.toBeEmpty();

  await hetidaDesigner.clearTest();
});
