import { expect, test } from '../fixtures/fixture';

test('Confirm release a workflow', async ({
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
  const workflowName = `Test release a workflow ${browserName}`;
  const workflowDescription = 'Releases a workflow';
  const workflowTag = '0.1.0';
  const workflowInputName = 'input';
  const workflowOutputName = 'output';
  const workflowInputData = '["MockData1","MockData2"]';
  const workflowDocumentation = `# ${workflowName}
## Description
${workflowDescription}
## Inputs
${workflowInputName}
## Outputs
${workflowOutputName}
## Examples
The json input of a typical call of this workflow is:
\`\`\`JSON
${workflowInputData}
\`\`\`
`;

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
  await hetidaDesigner.clickByTestId(
    `${workflowInputName}-value-input-wiring-dialog`
  );
  await hetidaDesigner.typeInJsonEditor(workflowInputData);
  await hetidaDesigner.clickByTestId('save-json-editor');

  // TODO: Wait for a change to happen
  // Wait for the store to update
  await page.waitForTimeout(3000);

  await hetidaDesigner.clickByTestId('execute-wiring-dialog');
  await page.waitForSelector('hd-protocol-viewer >> .protocol-content');
  const outputProtocol = await page
    .locator('hd-protocol-viewer >> .protocol-content >> span >> nth=1')
    .innerText();

  // Add workflow documentation
  await hetidaDesigner.clickIconInToolbar('Open documentation');
  await page.waitForSelector('hd-documentation-editor >> textarea');
  await hetidaDesigner.typeInDocumentationEditor(workflowDocumentation);
  await hetidaDesigner.clickByTestId('save-edit-documentation-editor');

  // Publish workflow
  await hetidaDesigner.clickTabInNavigation(1);
  await hetidaDesigner.clickIconInToolbar('Publish');
  await hetidaDesigner.clickByTestId('publish workflow-confirm-dialog');

  // Get released workflow details
  await hetidaDesigner.clickIconInToolbar('Edit workflow details');
  await page.waitForSelector(
    `mat-dialog-container:has-text("Edit workflow ${workflowName} ${workflowTag}")`
  );
  const workflowNameReleased = await page.inputValue('#name');
  const workflowCategoryReleased = await page.inputValue('#category');
  const workflowDescriptionReleased = await page.inputValue('#description');
  const workflowTagReleased = await page.inputValue('#tag');
  await hetidaDesigner.clickByTestId('cancel-copy-transformation-dialog');

  // Get released workflow I/O
  await hetidaDesigner.clickIconInToolbar('Configure I/O');
  await page.waitForSelector(
    `mat-dialog-container:has-text("Configure Input / Output for Workflow ${workflowName} ${workflowTag}")`
  );
  const workflowInputReleased = await page
    .getByTestId(
      `${componentInputName}-${componentName}-field-name-input-workflow-io-dialog`
    )
    .inputValue();
  const workflowOutputReleased = await page
    .getByTestId(
      `${componentOutputName}-${componentName}-field-name-output-workflow-io-dialog`
    )
    .inputValue();
  await hetidaDesigner.clickByTestId('cancel-workflow-io-dialog');

  // Get released workflow input data
  await hetidaDesigner.clickIconInToolbar('Execute');
  await page.waitForSelector(
    `mat-dialog-container:has-text("Execute Workflow ${workflowName} ${workflowTag}")`
  );
  await hetidaDesigner.clickByTestId(
    `${workflowInputName}-value-input-wiring-dialog`
  );
  const workflowInputDataReleased = await page
    .locator('.view-lines')
    .innerText();
  await hetidaDesigner.clickByTestId('cancel-json-editor');

  // Get released workflow protocol
  await hetidaDesigner.clickByTestId('execute-wiring-dialog');
  await page.waitForSelector('hd-protocol-viewer >> .protocol-content');
  const outputProtocolReleased = await page
    .locator('hd-protocol-viewer >> .protocol-content >> span >> nth=1')
    .innerText();

  // Get released workflow documentation
  await hetidaDesigner.clickIconInToolbar('Open documentation');
  await page.waitForSelector(
    'hd-documentation-editor >> .editor-and-preview__preview'
  );
  await hetidaDesigner.clickByTestId('save-edit-documentation-editor');
  const workflowDocumentationReleased = await page.inputValue(
    'hd-documentation-editor >> textarea'
  );

  // Assert
  // Edit details
  expect(workflowNameReleased).toEqual(workflowName);
  expect(workflowCategoryReleased).toEqual(workflowCategory);
  expect(workflowDescriptionReleased).toEqual(workflowDescription);
  expect(workflowTagReleased).toEqual(workflowTag);
  // Configure I/O
  expect(workflowInputReleased).toEqual(workflowInputName);
  expect(workflowOutputReleased).toEqual(workflowOutputName);
  // Execute
  expect(workflowInputDataReleased).toEqual(workflowInputData);
  expect(outputProtocolReleased).toEqual(outputProtocol);
  // Documentation
  expect(workflowDocumentationReleased).toEqual(workflowDocumentation);
});

test.afterEach(async ({ page, hetidaDesigner, browserName }) => {
  // Clear
  const workflowCategory = 'Test';
  const workflowName = `Test release a workflow ${browserName}`;
  const workflowTag = '0.1.0';

  await hetidaDesigner.clickWorkflowsInNavigation();
  await hetidaDesigner.clickCategoryInNavigation(workflowCategory);
  await hetidaDesigner.rightClickItemInNavigation(
    workflowCategory,
    workflowName
  );
  await page.locator('.mat-mdc-menu-panel').hover();
  await hetidaDesigner.clickOnContextMenu('Deprecate');
  await page.waitForSelector(
    `mat-dialog-container:has-text("Deprecate workflow ${workflowName} (${workflowTag})")`
  );
  await hetidaDesigner.clickByTestId('deprecate workflow-confirm-dialog');
  await hetidaDesigner.clearTest();
});
