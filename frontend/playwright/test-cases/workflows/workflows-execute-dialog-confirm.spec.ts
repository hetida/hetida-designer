import { test, expect } from '../fixtures/fixture';

test('Execute workflows, confirm dialog', async ({ page, hetidaDesigner }) => {
  // Arrange
  const categoryName = 'Examples';
  const workflowName = 'Volatility Detection Example';

  // Act
  await hetidaDesigner.clickWorkflowsComponentsInNavigation('Workflows');
  await hetidaDesigner.clickCategoryInNavigation(categoryName);
  await hetidaDesigner.doubleClickItemInNavigation(categoryName, workflowName);

  await hetidaDesigner.clickIconInToolbar('Execute');
  await page.waitForSelector('mat-dialog-container');

  await hetidaDesigner.clickAnyBtnInDialog('Execute');
  await page.waitForSelector('hd-protocol-viewer >> plotly-plot');

  // Assert
  const visibleProtocolViewer = page.locator('hd-protocol-viewer');
  await expect(visibleProtocolViewer).toBeVisible();

  const countPlotlyPlot = await page
    .locator('hd-protocol-viewer >> plotly-plot')
    .count();
  expect(countPlotlyPlot).toBeGreaterThan(0);

  await expect(visibleProtocolViewer).not.toBeEmpty();

  // Run clear
  await hetidaDesigner.clearTest();
});
