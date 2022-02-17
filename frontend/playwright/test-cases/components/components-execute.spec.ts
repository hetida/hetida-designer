import { test, expect } from '@playwright/test';
import { HetidaDesigner } from '../page-objects/hetida-designer';
import { Navigation } from '../page-objects/navigation';
import { ErrorNotification } from '../page-objects/error-notification';

test('Execute component', async ({ page }) => {
  const hetidaDesigner = new HetidaDesigner(page);
  const navigation = new Navigation(page);
  const errorNotification = new ErrorNotification(page);

  const categoryName = 'Arithmetic';
  const componentName = 'Pi';

  // Run setup
  await hetidaDesigner.setupTest();

  // Run test
  await navigation.clickBtnNavigation('components');
  // Expansion-panel expands on click
  await navigation.clickExpansionPanelNavigation(categoryName);
  // Open component on double-click
  await navigation.doubleClickItemNavigation(categoryName, componentName);

  // Execute component, click on icon "Execute"
  await navigation.clickIconToolbar('Execute');

  // Check if execute component dialog-container exists
  await page.waitForSelector('mat-dialog-container'); // Wait for dialog-container
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

  // Confirm execute component, click on button "Execute"
  await navigation.clickBtnDialog('Execute');

  // Check if error-notification occurred
  await errorNotification.checkErrorNotification();

  // Check if hd-protocol-viewer is visible
  const visibleProtocolViewer = page.locator('hd-protocol-viewer');
  await expect(visibleProtocolViewer).toBeVisible();
  // Check if hd-protocol-viewer contains a result
  await expect(visibleProtocolViewer).not.toBeEmpty();

  // Run clear
  await hetidaDesigner.clearTest();
});
