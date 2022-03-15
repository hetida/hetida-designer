import { test, expect } from '../fixtures/fixture';

test('Hover over workflow, load popover', async ({ page, hetidaDesigner }) => {
  // Arrange
  const categoryName = 'Examples';
  const workflowName = 'Volatility Detection Example';

  // Act
  await hetidaDesigner.clickWorkflowsComponentsInNavigation('Workflows');
  await hetidaDesigner.clickCategoryInNavigation(categoryName);

  await hetidaDesigner.hoverItemInNavigation(categoryName, workflowName);

  // Assert
  const popover = page.locator('hd-popover-base-item');
  await expect(popover).not.toBeEmpty();

  await hetidaDesigner.clearTest();
});
