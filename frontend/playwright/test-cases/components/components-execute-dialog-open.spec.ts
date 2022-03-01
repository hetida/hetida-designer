import { test, expect } from '@playwright/test';
import { HetidaDesigner } from '../page-objects/hetida-designer';
import { Navigation } from '../page-objects/navigation';

test('Execute components, open dialog-container', async ({ page }) => {
  const hetidaDesigner = new HetidaDesigner(page);
  const navigation = new Navigation(page);
  // Test parameter
  const categoryName = 'Arithmetic';
  const componentName = 'Pi';

  // Run setup
  await hetidaDesigner.setupTest();

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
