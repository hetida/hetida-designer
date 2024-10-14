import { expect, test } from '../fixtures/fixture';

test('Open "execute component" dialog', async ({ page, hetidaDesigner }) => {
  // Arrange
  const categoryName = 'Arithmetic';
  const componentName = 'Pi';

  // Act
  await hetidaDesigner.clickComponentsInNavigation();
  await hetidaDesigner.clickCategoryInNavigation(categoryName);
  await hetidaDesigner.doubleClickItemInNavigation(categoryName, componentName);

  await hetidaDesigner.clickIconInToolbar('Execute');
  await page.waitForSelector('mat-dialog-container');

  // Assert
  const countDialogContainer = await page
    .locator('mat-dialog-container')
    .count();
  expect(countDialogContainer).toEqual(1);

  // Check for equal substrings in dialog-title and opened tab
  const dialogTitle = page.locator('.mat-mdc-dialog-title h4');
  const componentTabName = await page
    .locator('div[role="tab"] >> nth=1')
    .locator('.text-ellipsis')
    .innerText();
  await expect(dialogTitle).toContainText(`${componentTabName}`);

  await hetidaDesigner.clearTest();
});
