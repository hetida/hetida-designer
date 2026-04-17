import { test, expect } from '../fixtures/fixture';

test('Hover over workflow, load popover', async ({ page, hetidaDesigner }) => {
  // Arrange
  const categoryName = 'Examples';
  const workflowName = 'Volatility Detection Example';
  const workflowTag = '1.0.0';

  // Act
  await hetidaDesigner.clickWorkflowsInNavigation();
  await hetidaDesigner.clickCategoryInNavigation(categoryName);

  await hetidaDesigner.hoverItemInNavigation(`${workflowName}(${workflowTag})`);

  // Assert
  const popover = page.locator('hd-popover-transformation');
  await expect(popover).not.toBeEmpty();

  await hetidaDesigner.clearTest();
});
