import { expect, test } from '../fixtures/fixture';

test('Open component on double-click', async ({ page, hetidaDesigner }) => {
  // Arrange
  const categoryName = 'Arithmetic';
  const componentName = 'Pi';

  // Act
  await hetidaDesigner.clickComponentsInNavigation();
  await hetidaDesigner.clickCategoryInNavigation(categoryName);

  await hetidaDesigner.doubleClickItemInNavigation(categoryName, componentName);
  await page.waitForSelector('hd-component-editor');

  // Assert
  // Check for equal names in list and opened tab
  const componentListName = await page
    .locator(`mat-expansion-panel:has-text("${categoryName}") >> nth=0`)
    .locator(`.navigation-item:has-text("${componentName}") >> nth=0`)
    .locator('.text-ellipsis')
    .innerText();
  const componentTabName = await page
    .locator('div[role="tab"] >> nth=1')
    .locator('.text-ellipsis')
    .innerText();
  expect(componentListName).toEqual(componentTabName);

  // Check if hd-component-editor exists
  const countComponentEditor = await page
    .locator('hd-component-editor')
    .count();
  expect(countComponentEditor).toEqual(1);

  await hetidaDesigner.clearTest();
});
