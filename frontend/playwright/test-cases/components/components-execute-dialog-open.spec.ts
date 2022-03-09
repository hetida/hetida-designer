import { test, expect } from '../fixtures/fixture';

test('Execute components, open dialog', async ({
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
  await navigation.doubleClickItemNavigation(categoryName, componentName);
  // Execute component, click on icon "Execute"
  await navigation.clickIconToolbar('Execute');
  await page.waitForSelector('mat-dialog-container'); // Wait for dialog-container

  // Check if execute component dialog-container exists
  const countDialogContainer = await page
    .locator('mat-dialog-container')
    .count();
  expect(countDialogContainer).toEqual(1);

  // Check for equal substrings in dialog-title and opened tab
  const dialogTitle = page.locator('.mat-dialog-title h4');
  const componentTabName = await page
    .locator('div[role="tab"] >> nth=1')
    .locator('.text-ellipsis')
    .innerText();
  await expect(dialogTitle).toContainText(`${componentTabName}`);

  // Run clear
  await hetidaDesigner.clearTest();
});
