import { expect, test } from '../fixtures/fixture';
test('Execute workflow with Optional Input and Default Value', async ({
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
  const workflowName = `Test execute a workflow ${browserName}`;
  const workflowDescription =
    'Execute a workflow with Optional Input and Default value';
  const workflowTag = '0.1.0';
  const workflowInputName = 'input';
  const workflowOutputName = 'output';
  const inputOptionValue = 'OPTIONAL';
  const inputDefaultValue = 'DefaultValueString';

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
  await hetidaDesigner.typeInInputByTestId(
    `${componentInputName}-${componentName}-field-name-input-workflow-io-dialog`,
    workflowInputName
  );
  await hetidaDesigner.selectItemInDropdown(
    `${componentInputName}-${componentName}-dynamic-fixed-workflow-io-dialog`,
    inputOptionValue
  );
  await hetidaDesigner.typeInInputByTestId(
    `${componentInputName}-optional-input-default-value-workflow-io-dialog`,
    inputDefaultValue
  );
  await hetidaDesigner.typeInInputByTestId(
    `${componentOutputName}-${componentName}-field-name-output-workflow-io-dialog`,
    workflowOutputName
  );
  await hetidaDesigner.clickByTestId('save-workflow-io-dialog');

  // Execute workflow and get the protocol
  await hetidaDesigner.clickIconInToolbar('Execute');
  await page.waitForSelector(
    `mat-dialog-container:has-text("Execute Workflow ${workflowName} ${workflowTag}")`
  );

  await hetidaDesigner.clickByTestId('execute-wiring-dialog');
  await page.waitForSelector('hd-protocol-viewer >> .protocol-content');
  const outputProtocol = await page
    .locator('hd-protocol-viewer >> .protocol-content >> span >> nth=1')
    .innerText()
    .then(text => text.replace('"', '').replace('"', ''));

  expect(outputProtocol).toBe(inputDefaultValue);
});

test.afterEach(async ({ page, hetidaDesigner, browserName }) => {
  // Clear
  const workflowCategory = 'Test';
  const workflowName = `Test execute a workflow ${browserName}`;
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
