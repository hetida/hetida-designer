import { test, expect } from '@playwright/test';
import { HetidaDesigner } from '../page-objects/hetida-designer';
import { Navigation } from '../page-objects/navigation';
import { ErrorNotification } from '../page-objects/error-notification';

test('Execute workflows, confirm dialog', async ({ page }) => {
  const hetidaDesigner = new HetidaDesigner(page);
  const navigation = new Navigation(page);
  const errorNotification = new ErrorNotification(page);
  // Test parameter
  const categoryName = 'Examples';
  const workflowName = 'Volatility Detection Example';

  // Run setup
  await hetidaDesigner.setupTest();

  // Run test
  await navigation.clickBtnNavigation('Workflows');
  await navigation.clickExpansionPanelNavigation(categoryName);
  await navigation.doubleClickItemNavigation(categoryName, workflowName);
  await navigation.clickIconToolbar('Execute');
  await page.waitForSelector('mat-dialog-container'); // Wait for dialog-container
  // Confirm execute workflow, click on button "Execute"
  await navigation.clickBtnDialog('Execute');
  await page.waitForSelector('hd-protocol-viewer >> plotly-plot'); // Wait for plotly-plot

  // Check if error-notification occurred
  const countErrorNotification = await errorNotification.checkErrorNotification();
  expect(countErrorNotification).toEqual(0);

  // Check if hd-protocol-viewer is visible
  const visibleProtocolViewer = page.locator('hd-protocol-viewer');
  await expect(visibleProtocolViewer).toBeVisible();

  // Check if plotly-plot exist in hd-protocol-viewer
  const countPlotlyPlot = await page
    .locator('hd-protocol-viewer >> plotly-plot')
    .count();
  expect(countPlotlyPlot).toBeGreaterThan(0);

  // Check if hd-protocol-viewer contains a result
  await expect(visibleProtocolViewer).not.toBeEmpty();

  // Run clear
  await hetidaDesigner.clearTest();
});
