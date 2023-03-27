const moment = require('moment');
import { expect, test } from '../fixtures/fixture';

test('Confirm execute workflow with type SERIES input and Python-Demo-Adapter as adapter selected', async ({
  page,
  hetidaDesigner
}) => {
  // Arrange
  const categoryName = 'Examples';
  const workflowName = 'Volatility Detection Example';
  const timestampRangeFrom = moment('2023-01-01T12:15Z', 'YYYY-MM-DD HH:mm');
  const timestampRangeTo = moment('2023-01-02T12:15Z', 'YYYY-MM-DD HH:mm');

  // Act
  await hetidaDesigner.clickWorkflowsComponentsInNavigation('Workflows');
  await hetidaDesigner.clickCategoryInNavigation(categoryName);
  await hetidaDesigner.doubleClickItemInNavigation(categoryName, workflowName);

  await hetidaDesigner.clickIconInToolbar('Execute');
  await page.waitForSelector(
    `mat-dialog-container:has-text("Execute Workflow Volatility Detection Example 1.0.0")`
  );

  await hetidaDesigner.selectItemInDropdown(
    'input_series-adapter-list-wiring-dialog',
    'Python-Demo-Adapter'
  );
  await hetidaDesigner.clickInput('input_series-browse-sources-wiring-dialog');
  await page.waitForSelector(`mat-dialog-container:has-text("Search Sources")`);

  await hetidaDesigner.typeInInput('search-tree-node', 'Influx Temperature');
  await hetidaDesigner.selectSourceSearchResult(0);
  await hetidaDesigner.clickCheckbox('input_series-node-wiring-context-menu');
  await page.mouse.click(0, 0); // close context menu
  await hetidaDesigner.clickButton('done-tree-node-modal');

  await hetidaDesigner.clickInput('input_series-timestamp-range-wiring-dialog');
  await hetidaDesigner.selectTimestampRange(
    timestampRangeFrom,
    timestampRangeTo
  );

  await hetidaDesigner.clickButton('execute-wiring-dialog');
  await page.waitForSelector('hd-protocol-viewer >> plotly-plot');

  // Assert
  const protocolViewer = page.locator('hd-protocol-viewer');
  await expect(protocolViewer).toBeVisible();

  const countPlotlyPlot = await page
    .locator('hd-protocol-viewer >> plotly-plot')
    .count();
  expect(countPlotlyPlot).toBeGreaterThan(0);

  await expect(protocolViewer).not.toBeEmpty();

  // Clear
  await hetidaDesigner.clickIconInToolbar('Execute');
  await page.waitForSelector(
    `mat-dialog-container:has-text("Execute Workflow Volatility Detection Example 1.0.0")`
  );
  await hetidaDesigner.clickButton('input_series-clear-input-wiring-dialog');
  await hetidaDesigner.clickInput('input_series-input-value-wiring-dialog');
  await page.waitForSelector(
    `mat-dialog-container:has-text("Json input for input_series")`
  );
  await hetidaDesigner.clickButton('save-json-editor');
  await hetidaDesigner.clickButton('execute-wiring-dialog');
  await page.waitForSelector('hd-protocol-viewer >> plotly-plot');

  await hetidaDesigner.clearTest();
});
