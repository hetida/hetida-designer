import { expect, test } from '../fixtures/fixture';

test('HDOS-364: releases a workflow or component', async ({
  page,
  hetidaDesigner,
  browserName
}) => {
  // Arrange
  const componentName = 'Pass Through';
  const componentCategory = 'Connectors';
  const workflowName = `Test Workflow HDOS-364 ${browserName}`;
  const workflowCategory = 'Test';
  const workflowDescription = 'Releases a workflow or component';
  const workflowTag = '1.0.1';
  const workflowInput = 'Input';
  const workflowOutput = 'Output';
  const workflowImportData = '["hello","world"]';

  const workflowDocumentation = `# Test Workflow HDOS-364 ${browserName}
## Description
Releases a workflow or component, e2e test.
## Inputs
${workflowInput}
## Outputs
${workflowOutput}
## Examples
The json input of a typical call of this workflow is:
\`\`\`JSON
${workflowImportData}
\`\`\`
`;

  // Act
  await hetidaDesigner.clickWorkflowsComponentsInNavigation('Workflows');
  await hetidaDesigner.clickAddWorkflowComponentInNavigation('Add workflow');
  await hetidaDesigner.typeInInput('name', workflowName);
  await hetidaDesigner.typeInInput('category', workflowCategory);
  await hetidaDesigner.typeInInput('description', workflowDescription);
  await hetidaDesigner.typeInInput('tag', workflowTag);
  await hetidaDesigner.clickButton('Create Workflow');

  await hetidaDesigner.clickWorkflowsComponentsInNavigation('Components');
  await hetidaDesigner.clickCategoryInNavigation(componentCategory);
  await hetidaDesigner.dragAndDropItemInNavigation(
    componentCategory,
    componentName,
    'hetida-flowchart'
  );

  await hetidaDesigner.clickIconInToolbar('Configure I/O');
  await page.waitForSelector('mat-dialog-container');
  await hetidaDesigner.typeInInputPosition(0, workflowInput);
  await hetidaDesigner.typeInInputPosition(1, workflowOutput);
  await hetidaDesigner.clickButton('Save');

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
  await hetidaDesigner.typeInTextareaPosition(0, workflowDocumentation);
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
  await hetidaDesigner.clickButton('Cancel', 1);
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
  expect(workflowInputReleased).toEqual(workflowInput);
  expect(workflowOutputReleased).toEqual(workflowOutput);
  // Execute
  expect(workflowImportDataReleased).toEqual(workflowImportData);
  expect(outputProtocolReleased).toEqual(outputProtocol);
  // Documentation
  expect(workflowDocumentationReleased).toEqual(workflowDocumentation);

  await hetidaDesigner.clickWorkflowsComponentsInNavigation('Workflows');
  await hetidaDesigner.clickCategoryInNavigation(workflowCategory);
  await hetidaDesigner.rightClickItemInNavigation(
    workflowCategory,
    workflowName
  );
  await page.locator('.mat-menu-panel').hover();
  await hetidaDesigner.clickOnContextMenu('Deprecate');
  await hetidaDesigner.clickButton('Deprecate workflow');
  await hetidaDesigner.clearTest();
});
