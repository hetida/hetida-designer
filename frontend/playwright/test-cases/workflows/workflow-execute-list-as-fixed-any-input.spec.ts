import { expect, test } from '../fixtures/fixture';

test('Confirm execute workflow with a list as fixed any input', async ({
  page,
  hetidaDesigner,
  browserName
}) => {
  // Arrange
  const componentCategory = 'Connectors';
  const componentName = 'Pass Through';
  const workflowCategory = 'Test';
  const workflowName = `Test list as fixed any input ${browserName}`;
  const workflowDescription = 'Use a list as fixed any input';
  const workflowTag = '0.1.0';
  const workflowImportData = '["MockData1","MockData2"]';

  // Act
  await hetidaDesigner.clickWorkflowsComponentsInNavigation('Workflows');
  await hetidaDesigner.clickAddWorkflowComponentInNavigation('Add workflow');
  await hetidaDesigner.typeInInput('name-copy-transformation-dialog', workflowName);
  await hetidaDesigner.typeInInput('category-copy-transformation-dialog', workflowCategory);
  await hetidaDesigner.typeInInput('description-copy-transformation-dialog', workflowDescription);
  await hetidaDesigner.typeInInput('tag-copy-transformation-dialog', workflowTag);
  await hetidaDesigner.clickByTestId(
    'create workflow-copy-transformation-dialog'
  );

  await hetidaDesigner.clickWorkflowsComponentsInNavigation('Components');
  await hetidaDesigner.clickCategoryInNavigation(componentCategory);
  await hetidaDesigner.dragAndDropItemInNavigation(
    componentCategory,
    componentName,
    'hetida-flowchart'
  );

  await hetidaDesigner.clickIconInToolbar('Configure I/O');
  await page.waitForSelector(
    `mat-dialog-container:has-text("Configure Input / Output for Workflow ${workflowName} ${workflowTag}")`
  );
  await hetidaDesigner.clickByTestId(
    'input-pass through-dynamic-fixed-workflow-io-dialog'
  );
  await hetidaDesigner.clickByTestId(
    'input-pass through-input-data-workflow-io-dialog'
  );
  await hetidaDesigner.importJson(workflowImportData);
  await hetidaDesigner.clickByTestId('save-json-editor');
  await hetidaDesigner.typeInInput(
    'output-pass through-field-name-output-workflow-io-dialog',
    'Output'
  );
  await hetidaDesigner.clickByTestId('save-workflow-io-dialog');

  await hetidaDesigner.clickIconInToolbar('Execute');
  await page.waitForSelector(
    `mat-dialog-container:has-text("Execute Workflow ${workflowName} ${workflowTag}")`
  );
  await hetidaDesigner.clickByTestId('execute-wiring-dialog');
  await page.waitForSelector('hd-protocol-viewer >> .protocol-content');

  // Assert
  const output = await page
    .locator('hd-protocol-viewer >> .protocol-content >> span >> nth=1')
    .innerText();
  expect(output).toEqual(workflowImportData);
});

test.afterEach(async ({ page, hetidaDesigner, browserName }) => {
  // Clear
  const workflowCategory = 'Test';
  const workflowName = `Test list as fixed any input ${browserName}`;
  const workflowTag = '0.1.0';

  await hetidaDesigner.clickWorkflowsComponentsInNavigation('Workflows');
  await hetidaDesigner.clickCategoryInNavigation(workflowCategory);
  await hetidaDesigner.rightClickItemInNavigation(
    workflowCategory,
    workflowName
  );
  await page.locator('.mat-menu-panel').hover();
  await hetidaDesigner.clickOnContextMenu('Delete');
  await page.waitForSelector(
    `mat-dialog-container:has-text("Delete workflow ${workflowName} ${workflowTag}")`
  );
  await hetidaDesigner.clickByTestId('delete workflow-confirm-dialog');

  await hetidaDesigner.clearTest();
});
