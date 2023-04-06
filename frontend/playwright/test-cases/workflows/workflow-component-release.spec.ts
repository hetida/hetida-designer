import { expect, test } from '../fixtures/fixture';

test('Confirm release a workflow or component', async ({
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
  const workflowDescription = 'Releases a workflow or component';
  const workflowTag = '0.1.1';
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
  await hetidaDesigner.clickWorkflowsComponentsInNavigation('Workflows');
  await hetidaDesigner.clickAddWorkflowComponentInNavigation('Add workflow');
  await page.waitForSelector(
    `mat-dialog-container:has-text("Create new workflow")`
  );
  await hetidaDesigner.typeInInputById('name', workflowName);
  await hetidaDesigner.typeInInputById('category', workflowCategory);
  await hetidaDesigner.typeInInputById('description', workflowDescription);
  await hetidaDesigner.typeInInputById('tag', workflowTag);
  await hetidaDesigner.clickByTestId(
    'create workflow-copy-transformation-dialog'
  );

  await hetidaDesigner.clickWorkflowsComponentsInNavigation('Components');
  await hetidaDesigner.clickCategoryInNavigation(componentCategory);
  await hetidaDesigner.dragAndDropItemInNavigation(
    componentCategory,
    `${componentName} (${componentTag})`
  );

  await hetidaDesigner.clickIconInToolbar('Configure I/O');
  await page.waitForSelector(
    `mat-dialog-container:has-text("Configure Input / Output for Workflow ${workflowName} ${workflowTag}")`
  );
  await hetidaDesigner.typeInInputByTestId(`${componentInputName}-${componentName}-field-name-input-workflow-io-dialog`, workflowInputName);
  await hetidaDesigner.typeInInputByTestId(`${componentOutputName}-${componentName}-field-name-output-workflow-io-dialog`, workflowOutputName);
  await hetidaDesigner.clickByTestId('save-workflow-io-dialog');

  await hetidaDesigner.clickIconInToolbar('Execute');
  await page.waitForSelector('mat-dialog-container');
  await hetidaDesigner.clickInput(0);
  await hetidaDesigner.importJson(workflowImportData);
  await hetidaDesigner.clickButton('Save');
  await hetidaDesigner.clickButton('Execute');
  await page.waitForSelector('hd-protocol-viewer >> .protocol-content');
  const outputProtocol = await page
    .locator('hd-protocol-viewer >> .protocol-content >> span >> nth=1')
    .innerText();

  await hetidaDesigner.clickIconInToolbar('Open documentation');
  await page.waitForSelector('hd-documentation-editor-dialog >> textarea');
  await hetidaDesigner.typeInDocumentationEditor(workflowDocumentation);
  await hetidaDesigner.clickButton('Save');

  await hetidaDesigner.clickTabInNavigation(1);
  await hetidaDesigner.clickIconInToolbar('Publish');
  await hetidaDesigner.clickButton('Publish workflow');

  await hetidaDesigner.clickIconInToolbar('Edit workflow details');
  await page.waitForSelector('mat-dialog-container');
  const workflowNameReleased = await page.inputValue('#name');
  const workflowCategoryReleased = await page.inputValue('#category');
  const workflowDescriptionReleased = await page.inputValue('#description');
  const workflowTagReleased = await page.inputValue('#tag');
  await hetidaDesigner.clickButton('Cancel');

  await hetidaDesigner.clickIconInToolbar('Configure I/O');
  await page.waitForSelector('mat-dialog-container');
  const workflowInputReleased = await page.inputValue(
    'input[type="text"] >> nth=0'
  );
  const workflowOutputReleased = await page.inputValue(
    'input[type="text"] >> nth=1'
  );
  await hetidaDesigner.clickButton('Cancel');

  await hetidaDesigner.clickIconInToolbar('Execute');
  await page.waitForSelector('mat-dialog-container');
  await hetidaDesigner.clickInput(0);
  const workflowImportDataReleased = await page
    .locator('.view-lines')
    .innerText();
  await hetidaDesigner.clickButtonPosition(1, 'Cancel');
  await hetidaDesigner.clickButton('Execute');
  await page.waitForSelector('hd-protocol-viewer >> .protocol-content');
  const outputProtocolReleased = await page
    .locator('hd-protocol-viewer >> .protocol-content >> span >> nth=1')
    .innerText();

  await hetidaDesigner.clickIconInToolbar('Open documentation');
  await page.waitForSelector(
    'hd-documentation-editor-dialog >> .editor-and-preview__preview'
  );
  await hetidaDesigner.clickButton('Edit');
  const workflowDocumentationReleased = await page.inputValue('textarea');

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
  expect(workflowImportDataReleased).toEqual(workflowInputData);
  expect(outputProtocolReleased).toEqual(outputProtocol);
  // Documentation
  expect(workflowDocumentationReleased).toEqual(workflowDocumentation);
});

test.afterEach(async ({ page, hetidaDesigner, browserName }) => {
    // Clear
    const workflowCategory = 'Test';
    const workflowName = `Test release a workflow ${browserName}`;
    const workflowTag = '0.1.1';

    await hetidaDesigner.clickWorkflowsComponentsInNavigation('Workflows');
    await hetidaDesigner.clickCategoryInNavigation(workflowCategory);
    await hetidaDesigner.rightClickItemInNavigation(
      workflowCategory,
      workflowName
    );
    await page.locator('.mat-menu-panel').hover();
    await hetidaDesigner.clickOnContextMenu('Deprecate');
    await page.waitForSelector(
      `mat-dialog-container:has-text("Deprecate workflow ${workflowName} (${workflowTag})")`
    );
    await hetidaDesigner.clickByTestId('deprecate workflow-confirm-dialog');
  
    await hetidaDesigner.clearTest();
});
