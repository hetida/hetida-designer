import { expect, test } from '../fixtures/fixture';

test('Load component list', async ({ page, hetidaDesigner }) => {
  // Arrange
  // Act
  await hetidaDesigner.clickWorkflowsComponentsInNavigation('Components');

  // Assert
  const countComponents = await page.locator('hd-navigation-category').count();
  expect(countComponents).toBeGreaterThan(0);

  await hetidaDesigner.clearTest();
});
