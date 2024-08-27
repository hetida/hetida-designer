import { expect, test } from '../fixtures/fixture';

test('Open "execute workflow" dialog', async ({ page, hetidaDesigner }) => {
  // Arrange
  const categoryName = 'Examples';
  const workflowName = 'Volatility Detection Example';

  // Act
  await hetidaDesigner.clickWorkflowsInNavigation();
  await hetidaDesigner.clickCategoryInNavigation(categoryName);
  await hetidaDesigner.doubleClickItemInNavigation(categoryName, workflowName);

  await hetidaDesigner.clickIconInToolbar('Execute');
  await page.waitForSelector('mat-dialog-container');

  // Assert
  const countDialogContainer = await page
    .locator('mat-dialog-container')
    .count();
  expect(countDialogContainer).toEqual(1);

  // Check for equal substrings in dialog-title and opened tab
  const dialogTitle = page.locator('.mat-mdc-dialog-title h4');
  const workflowTabName = await page
    .locator('div[role="tab"] >> nth=1')
    .locator('.text-ellipsis')
    .innerText();
  await expect(dialogTitle).toContainText(`${workflowTabName}`);

  await hetidaDesigner.clearTest();
});
