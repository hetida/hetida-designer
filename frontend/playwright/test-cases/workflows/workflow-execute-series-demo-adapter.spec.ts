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
  const labelName = 'input_series';
  const timestampRangeFrom = moment('2023-01-01T12:15Z', 'YYYY-MM-DD HH:mm');
  const timestampRangeTo = moment('2023-01-02T12:15Z', 'YYYY-MM-DD HH:mm');

  // Act
  await hetidaDesigner.clickWorkflowsComponentsInNavigation('Workflows');
  await hetidaDesigner.clickCategoryInNavigation(categoryName);
  await hetidaDesigner.doubleClickItemInNavigation(categoryName, workflowName);

  await hetidaDesigner.clickIconInToolbar('Execute');
  await page.waitForSelector(
    `mat-dialog-container:has-text("Execute Workflow ${workflowName} ${workflowTag}")`
  );

  await hetidaDesigner.selectItemInDropdown(
    `${labelName}-adapter-list-input-wiring-dialog`,
    'Python-Demo-Adapter'
  );
  await hetidaDesigner.clickByTestId(
    `${labelName}-browse-sources-input-wiring-dialog`
  );
  await page.waitForSelector('mat-dialog-container:has-text("Search Sources")');

  await hetidaDesigner.typeInInput('search-tree-node', 'Influx Temperature');
  await hetidaDesigner.selectSourceSearchResult(0);
  await hetidaDesigner.clickByTestId(`${labelName}-node-wiring-context-menu`);
  await page.mouse.click(0, 0); // close context menu
  await hetidaDesigner.clickByTestId('done-tree-node-modal');

  await hetidaDesigner.clickByTestId(
    `${labelName}-timestamp-range-input-wiring-dialog`
  );
  await hetidaDesigner.selectTimestampRange(
    timestampRangeFrom,
    timestampRangeTo
  );

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
  const labelName = 'input_series';

  await hetidaDesigner.clickIconInToolbar('Execute');
  await page.waitForSelector(
    `mat-dialog-container:has-text("Execute Workflow ${workflowName} ${workflowTag}")`
  );
  await hetidaDesigner.clickByTestId(`${labelName}-clear-input-wiring-dialog`);
  await hetidaDesigner.clickByTestId(`${labelName}-value-input-wiring-dialog`);
  await page.waitForSelector(
    `mat-dialog-container:has-text("Json input for ${labelName}")`
  );
  await hetidaDesigner.clickByTestId('save-json-editor');
  await hetidaDesigner.clickByTestId('execute-wiring-dialog');
  await page.waitForSelector('hd-protocol-viewer >> plotly-plot');

  await hetidaDesigner.clearTest();
});
