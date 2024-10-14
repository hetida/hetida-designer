import { expect, test } from '../fixtures/fixture';

test('Confirm execute workflow with a list as fixed any input', async ({
  page,
  hetidaDesigner,
  browserName
}) => {
  // Arrange
  const componentCategory = 'Connectors';
  const componentName = 'pass through';
  const componentTag = '1.0.0';
  const componentInputName = 'input';
  const componentOutputName = 'output';
  const workflowCategory = 'Test';
  const workflowName = `Test list as fixed any input ${browserName}`;
  const workflowDescription = 'Use a list as fixed any input';
  const workflowTag = '0.1.0';
  const workflowInputData = '["MockData1","MockData2"]';
  const workflowOutputName = 'output';

  // Act
  // Add a new test workflow
  await hetidaDesigner.clickWorkflowsInNavigation();
  await hetidaDesigner.clickAddButtonInNavigation('Add workflow');
  await page.waitForSelector(
    'mat-dialog-container:has-text("Create new workflow")'
  );
  await hetidaDesigner.typeInInputById('name', workflowName);
  await hetidaDesigner.typeInInputById('category', workflowCategory);
  await hetidaDesigner.typeInInputById('description', workflowDescription);
  await hetidaDesigner.typeInInputById('tag', workflowTag);
  await hetidaDesigner.clickByTestId(
    'create workflow-copy-transformation-dialog'
  );

  // Add a component to the workflow
  await hetidaDesigner.clickComponentsInNavigation();
  await hetidaDesigner.clickCategoryInNavigation(componentCategory);
  await hetidaDesigner.dragAndDropItemFromNavigationToFlowchart(
    componentCategory,
    `${componentName} (${componentTag})`
  );

  // Configure workflow I/O
  await hetidaDesigner.clickIconInToolbar('Configure I/O');
  await page.waitForSelector(
    `mat-dialog-container:has-text("Configure Input / Output for Workflow ${workflowName} ${workflowTag}")`
  );
  await hetidaDesigner.selectItemInDropdown(
    `${componentInputName}-${componentName}-dynamic-fixed-workflow-io-dialog`,
    'FIXED'
  );
  await hetidaDesigner.clickByTestId(
    `${componentInputName}-${componentName}-input-data-workflow-io-dialog`
  );
  await hetidaDesigner.typeInJsonEditor(workflowInputData);
  await hetidaDesigner.clickByTestId('save-json-editor');
  await hetidaDesigner.typeInInputByTestId(
    `${componentOutputName}-${componentName}-field-name-output-workflow-io-dialog`,
    workflowOutputName
  );
  await hetidaDesigner.clickByTestId('save-workflow-io-dialog');

  // Execute workflow
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
  expect(output).toEqual(workflowInputData);
});

test.afterEach(async ({ page, hetidaDesigner, browserName }) => {
  // Clear
  const workflowCategory = 'Test';
  const workflowName = `Test list as fixed any input ${browserName}`;
  const workflowTag = '0.1.0';

  await hetidaDesigner.clickWorkflowsInNavigation();
  await hetidaDesigner.clickCategoryInNavigation(workflowCategory);
  await hetidaDesigner.rightClickItemInNavigation(
    workflowCategory,
    workflowName
  );
  await page.locator('.mat-mdc-menu-panel').hover();
  await hetidaDesigner.clickOnContextMenu('Delete');
  await page.waitForSelector(
    `mat-dialog-container:has-text("Delete workflow ${workflowName} (${workflowTag})")`
  );
  await hetidaDesigner.clickByTestId('delete workflow-confirm-dialog');

  await hetidaDesigner.clearTest();
});
