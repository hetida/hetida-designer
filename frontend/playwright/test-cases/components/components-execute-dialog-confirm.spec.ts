import { test, expect } from '@playwright/test';
import { HetidaDesigner } from '../page-objects/hetida-designer';
import { Navigation } from '../page-objects/navigation';
import { ErrorNotification } from '../page-objects/error-notification';

test('Execute components, confirm dialog-container', async ({ page }) => {
  const hetidaDesigner = new HetidaDesigner(page);
  const navigation = new Navigation(page);
  const errorNotification = new ErrorNotification(page);
  // Test parameter
  const categoryName = 'Arithmetic';
  const componentName = 'Pi';

  // Run setup
  await hetidaDesigner.setupTest();

  // Run test
  await navigation.clickBtnNavigation('Components');
  await navigation.clickExpansionPanelNavigation(categoryName);
  await navigation.doubleClickItemNavigation(categoryName, componentName);
  await navigation.clickIconToolbar('Execute');
  // Confirm execute component, click on button "Execute"
  await navigation.clickBtnDialog('Execute');

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
