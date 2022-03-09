import { test, expect } from '../fixtures/fixture';

test('Execute components, confirm dialog', async ({
  page,
  hetidaDesigner,
  navigation,
  errorNotification
}) => {
  // Test parameter
  const categoryName = 'Arithmetic';
  const componentName = 'Pi';

  // Run test
  await navigation.clickBtnNavigation('Components');
  await navigation.clickExpansionPanelNavigation(categoryName);
  await navigation.doubleClickItemNavigation(categoryName, componentName);
  await navigation.clickIconToolbar('Execute');
  await page.waitForSelector('mat-dialog-container'); // Wait for dialog-container
  // Confirm execute component, click on button "Execute"
  await navigation.clickBtnDialog('Execute');
  await page.waitForSelector('hd-protocol-viewer'); // Wait for hd-protocol-viewer

  // Check if error-notification occurred
  const countErrorNotification = await errorNotification.checkErrorNotification();
  expect(countErrorNotification).toEqual(0);

  // Check if hd-protocol-viewer is visible
  const visibleProtocolViewer = page.locator('hd-protocol-viewer');
  await expect(visibleProtocolViewer).toBeVisible();

  // Check if hd-protocol-viewer contains a result
  await expect(visibleProtocolViewer).not.toBeEmpty();

  // Run clear
  await hetidaDesigner.clearTest();
});
