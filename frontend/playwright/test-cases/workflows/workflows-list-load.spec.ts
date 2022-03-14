import { test, expect } from '../fixtures/fixture';

test('Load workflows list', async ({ page, hetidaDesigner }) => {
  // Arrange
  // Act
  await hetidaDesigner.clickWorkflowsComponentsInNavigation('Workflows');

  // Assert
  const countWorkflows = await page.locator('hd-navigation-category').count();
  expect(countWorkflows).toBeGreaterThan(0);

  // Run clear
  await hetidaDesigner.clearTest();
});
