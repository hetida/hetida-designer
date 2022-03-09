import { test, expect } from '../fixtures/fixture';

test('Open components on double-click', async ({
  page,
  hetidaDesigner,
  navigation
}) => {
  // Test parameter
  const categoryName = 'Arithmetic';
  const componentName = 'Pi';

  // Run test
  await navigation.clickBtnNavigation('Components');
  await navigation.clickExpansionPanelNavigation(categoryName);
  // Open component on double-click
  await navigation.doubleClickItemNavigation(categoryName, componentName);
  await page.waitForSelector('hd-component-editor'); // Wait for hd-component-editor

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

  // Run clear
  await hetidaDesigner.clearTest();
});
