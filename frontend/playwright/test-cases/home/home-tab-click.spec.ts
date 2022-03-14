import { test, expect } from '../fixtures/fixture';

test('Click on home tab', async ({ page, hetidaDesigner }) => {
  // Arrange
  // Act
  await hetidaDesigner.clickTabInNavigation(0);

  // Assert
  const homeHeader = page.locator('.home-header h1');
  await expect(homeHeader).toHaveText('Welcome to hetida designer');

  // Run clear
  await hetidaDesigner.clearTest();
});
