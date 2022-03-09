import { test, expect } from '../fixtures/fixture';

test('Execute workflows, open dialog', async ({
  page,
  hetidaDesigner,
  navigation
}) => {
  // Test parameter
  const categoryName = 'Examples';
  const workflowName = 'Volatility Detection Example';

  // Run test
  await navigation.clickBtnNavigation('Workflows');
  await navigation.clickExpansionPanelNavigation(categoryName);
  await navigation.doubleClickItemNavigation(categoryName, workflowName);
  // Execute workflow, click on icon "Execute"
  await navigation.clickIconToolbar('Execute');
  await page.waitForSelector('mat-dialog-container'); // Wait for dialog-container

  // Check if execute workflow dialog-container exists
  const countDialogContainer = await page
    .locator('mat-dialog-container')
    .count();
  expect(countDialogContainer).toEqual(1);

  // Check for equal substrings in dialog-title and opened tab
  const dialogTitle = page.locator('.mat-dialog-title h4');
  const workflowTabName = await page
    .locator('div[role="tab"] >> nth=1')
    .locator('.text-ellipsis')
    .innerText();
  await expect(dialogTitle).toContainText(`${workflowTabName}`);

  // Run clear
  await hetidaDesigner.clearTest();
});
