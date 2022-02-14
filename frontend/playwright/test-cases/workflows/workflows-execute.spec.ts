import { test, expect } from '@playwright/test';
import { HetidaDesigner } from '../page-objects/hetida-designer';
import { Navigation } from '../page-objects/navigation';

test('Execute workflow', async ({ page }) => {
  const hetidaDesigner = new HetidaDesigner(page);
  const navigation = new Navigation(page);

  const categoryName = 'Examples';
  const workflowName = 'Volatility Detection Example';

  // Run setup
  await hetidaDesigner.setupTest();

  // Run test
  await navigation.clickBtnNavigation('workflows');
  // Expansion-panel expands on click
  await navigation.clickExpansionPanelNavigation(categoryName);
  // Open workflow on double-click
  await navigation.doubleClickItemNavigation(categoryName, workflowName);

  // Execute workflow, click on icon "Execute"
  await navigation.clickIconToolbar('Execute');

  // Check if execute workflow dialog-container exists
  await page.waitForSelector('mat-dialog-container');// Wait for dialog-container
  const countDialogContainer = await page.locator('mat-dialog-container').count();
  expect(countDialogContainer).toEqual(1);

  // Check for equal substrings in dialog-title and opened tab
  const dialogTitle = page.locator('.mat-dialog-title h4');
  const componentTabName = await page.locator('div[role="tab"] >> nth=1').locator('.text-ellipsis').innerText();
  await expect(dialogTitle).toContainText(`${componentTabName}`);

  // Confirm execute workflow, click on button "Execute"
  await navigation.clickBtnDialog('Execute');
  // Check if hd-protocol-viewer is visible
  const visibleProtocolViewer = page.locator('hd-protocol-viewer');
  await expect(visibleProtocolViewer).toBeVisible();
  // Check if plotly-plot exist in hd-protocol-viewer
  const countPlotlyPlot = await page.locator('hd-protocol-viewer >> plotly-plot').count();
  expect(countPlotlyPlot).toBeGreaterThan(0);

  // Run clear
  await hetidaDesigner.clearTest();
});
