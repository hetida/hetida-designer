import { test, expect } from '../fixtures/fixture';

test('Search for components', async ({ page, hetidaDesigner }) => {
  // Arrange
  const categoryName = 'Arithmetic';
  const componentName = 'Pi'; // Search term

  // Act
  await hetidaDesigner.clickWorkflowsComponentsInNavigation('Components');
  await hetidaDesigner.typeInSearchTerm(componentName);
  // Expansion-panel expands on click, to render and locat components
  await hetidaDesigner.clickCategoryInNavigation(categoryName);

  // Assert
  // Check if components-list is filtered
  const countComponents = await page.locator('hd-navigation-category').count();
  expect(countComponents).toBeGreaterThan(0);

  // Check for equal names in first component found, in list and search term
  const firstComponentListName = await page
    .locator('mat-expansion-panel >> nth=0')
    .locator('.navigation-item >> nth=0')
    .locator('.text-ellipsis')
    .innerText();
  expect(firstComponentListName).toEqual(componentName);

  // Run clear
  await hetidaDesigner.clearTest();
});
