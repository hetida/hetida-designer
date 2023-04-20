const moment = require('moment');
import { expect, test } from '../fixtures/fixture';

test('Confirm execute workflow with type SERIES input and Python-Demo-Adapter selected', async ({
  page,
  hetidaDesigner
}) => {
  // Arrange
  const categoryName = 'Examples';
  const workflowName = 'Volatility Detection Example';
  const workflowTag = '1.0.0';
  const workflowInputName = 'input_series';
  const adapter = 'Python-Demo-Adapter';
  const source = 'Influx Temperature';
  const timestampRangeFrom = moment('2023-01-01T12:15Z', 'YYYY-MM-DD HH:mm');
  const timestampRangeTo = moment('2023-01-02T12:15Z', 'YYYY-MM-DD HH:mm');

  // Act
  // Open workflow
  await hetidaDesigner.clickWorkflowsInNavigation();
  await hetidaDesigner.clickCategoryInNavigation(categoryName);
  await hetidaDesigner.doubleClickItemInNavigation(categoryName, workflowName);

  // Open execute workflow dialog
  await hetidaDesigner.clickIconInToolbar('Execute');
  await page.waitForSelector(
    `mat-dialog-container:has-text("Execute Workflow ${workflowName} ${workflowTag}")`
  );

  // Select adapter
  await hetidaDesigner.selectItemInDropdown(
    `${workflowInputName}-adapter-list-input-wiring-dialog`,
    adapter
  );

  // Select source
  await hetidaDesigner.clickByTestId(
    `${workflowInputName}-browse-sources-input-wiring-dialog`
  );
  await page.waitForSelector('mat-dialog-container:has-text("Search Sources")');
  await hetidaDesigner.typeInInputByTestId('search-tree-node', source);
  await hetidaDesigner.selectSourceSearchResult(0);
  await hetidaDesigner.clickByTestId(
    `${workflowInputName}-node-wiring-context-menu`
  );
  await page.mouse.click(0, 0); // Close context menu
  await hetidaDesigner.clickByTestId('done-tree-node-modal');

  // Select timestamp range
  await hetidaDesigner.clickByTestId(
    `${workflowInputName}-timestamp-range-input-wiring-dialog`
  );
  await hetidaDesigner.selectTimestampRange(
    timestampRangeFrom,
    timestampRangeTo
  );

  // Execute workflow
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
});

test.afterEach(async ({ page, hetidaDesigner }) => {
  // Clear
  const workflowName = 'Volatility Detection Example';
  const workflowTag = '1.0.0';
  const workflowInputName = 'input_series';

  await hetidaDesigner.clickIconInToolbar('Execute');
  await page.waitForSelector(
    `mat-dialog-container:has-text("Execute Workflow ${workflowName} ${workflowTag}")`
  );
  await hetidaDesigner.clickByTestId(
    `${workflowInputName}-clear-input-wiring-dialog`
  );
  await hetidaDesigner.clickByTestId(
    `${workflowInputName}-value-input-wiring-dialog`
  );
  await page.waitForSelector(
    `mat-dialog-container:has-text("Json input for ${workflowInputName}")`
  );
  await hetidaDesigner.clickByTestId('save-json-editor');
  await hetidaDesigner.clickByTestId('execute-wiring-dialog');
  await page.waitForSelector('hd-protocol-viewer >> plotly-plot');

  await hetidaDesigner.clearTest();
});
