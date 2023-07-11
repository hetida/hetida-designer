import { expect, test } from '../fixtures/fixture';

test('Confirm "execute workflow" dialog', async ({ page, hetidaDesigner }) => {
  // Arrange
  const categoryName = 'Examples';
  const workflowName = 'Volatility Detection Example';

  // Act
  await hetidaDesigner.clickWorkflowsInNavigation();
  await hetidaDesigner.clickCategoryInNavigation(categoryName);
  await hetidaDesigner.doubleClickItemInNavigation(categoryName, workflowName);

  await hetidaDesigner.clickIconInToolbar('Execute');
  await page.waitForSelector('mat-dialog-container');

  await hetidaDesigner.clickByTestId('execute-wiring-dialog');
  await page.waitForSelector('hd-protocol-viewer >> plotly-plot');

  // Assert
  const protocolViewer = page.locator('hd-protocol-viewer');
  await expect(protocolViewer).toBeVisible();

  const countPlotlyPlot = await page
    .locator('hd-protocol-viewer >> plotly-plot')
    .count();
  expect(countPlotlyPlot).toBeGreaterThan(0);

  await expect(protocolViewer).not.toBeEmpty();

  await hetidaDesigner.clearTest();
});
