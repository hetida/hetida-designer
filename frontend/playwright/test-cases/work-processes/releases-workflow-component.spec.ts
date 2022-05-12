import { expect, test } from '../fixtures/fixture';

test('HDOS-364: releases workflow or component', async ({
  page,
  hetidaDesigner
}) => {
  // Arrange
  const componentName = 'Pass Through';
  const componentCategoryName = 'Connectors';
  const workflowName = 'Test Workflow HDOS-364';
  const workflowCategoryName = 'Test';
  const workflowDescription = 'Releases workflow or component';
  const workflowTag = '1.0.1';
  const workflowInput = 'Input';
  const workflowOutput = 'Output';
  const workflowInputImportData = '["hello","world"]';

  const workflowDocumentation = `# Test Workflow HDOS-364
## Description
Releases workflow or component e2e test.
## Inputs
${workflowInput}
## Outputs
${workflowOutput}
## Examples
The json input of a typical call of this workflow is:
\`\`\`JSON
${workflowInputImportData}
\`\`\`
`;

  // Act
  await hetidaDesigner.clickWorkflowsComponentsInNavigation('Workflows');
  await hetidaDesigner.clickAddWorkflowComponentInNavigation('Add workflow');
  await hetidaDesigner.typeInInput('name', workflowName);
  await hetidaDesigner.typeInInput('category', workflowCategoryName);
  await hetidaDesigner.typeInInput('description', workflowDescription);
  await hetidaDesigner.typeInInput('tag', workflowTag);
  await hetidaDesigner.clickButton('Create Workflow');

  await hetidaDesigner.clickWorkflowsComponentsInNavigation('Components');
  await hetidaDesigner.clickCategoryInNavigation(componentCategoryName);
  await hetidaDesigner.dragAndDropItemInNavigation(
    componentCategoryName,
    componentName,
    'hetida-flowchart'
  );

  await hetidaDesigner.clickIconInToolbar('Configure I/O');
  await page.waitForSelector('mat-dialog-container', {
    state: 'attached',
    timeout: 5000
  });
  await hetidaDesigner.typeInInputPosition(0, workflowInput);
  await hetidaDesigner.typeInInputPosition(1, workflowOutput);
  await hetidaDesigner.clickButton('Save');

  await hetidaDesigner.clickIconInToolbar('Execute');
  await page.waitForSelector('mat-dialog-container');
  await hetidaDesigner.clickInput(0);
  await hetidaDesigner.importJson(workflowInputImportData);
  await hetidaDesigner.clickButton('Save');
  await hetidaDesigner.clickButton('Execute');
  await page.waitForSelector('hd-protocol-viewer >> .protocol-content');
  const outputDraft = await page
    .locator('hd-protocol-viewer >> .protocol-content >> span >> nth=1')
    .innerText();

  await hetidaDesigner.clickIconInToolbar('Open documentation');
  await page.waitForSelector('hd-documentation-editor-dialog >> textarea');
  await hetidaDesigner.typeInTextareaPosition(0, workflowDocumentation);
  await hetidaDesigner.clickButton('Save');

  await hetidaDesigner.clickTabInNavigation(0);
  // await hetidaDesigner.clickIconInToolbar('Publish');
  // await hetidaDesigner.clickButton('Publish workflow');

  await hetidaDesigner.clickIconInToolbar('Edit workflow details');
  await page.waitForSelector('mat-dialog-container');
  const workflowNameReleased = page.locator('');
  await hetidaDesigner.clickButton('Cancel');

  await hetidaDesigner.clickIconInToolbar('Configure I/O');
  await page.waitForSelector('mat-dialog-container', {
    state: 'attached',
    timeout: 5000
  });
  await hetidaDesigner.clickButton('Cancel');

  await hetidaDesigner.clickIconInToolbar('Execute');
  await page.waitForSelector('mat-dialog-container');
  await hetidaDesigner.clickInput(0);
  await hetidaDesigner.clickButton('Save');
  await hetidaDesigner.clickButton('Execute');
  await page.waitForSelector('hd-protocol-viewer >> .protocol-content');
  const outputReleased = await page
    .locator('hd-protocol-viewer >> .protocol-content >> span >> nth=1')
    .innerText();

  await hetidaDesigner.clickIconInToolbar('Open documentation');
  await page.waitForSelector('hd-documentation-editor-dialog >> textarea');

  // Assert
  // Edit details
  // Configure I/O
  // Execute
  // Documentation

  await hetidaDesigner.clickWorkflowsComponentsInNavigation('Workflows');
  await hetidaDesigner.clickCategoryInNavigation(workflowCategoryName);
  await hetidaDesigner.rightClickItemInNavigation(
    workflowCategoryName,
    workflowName
  );
  await page.locator('.mat-menu-panel').hover();
  await hetidaDesigner.clickOnContextMenu('Deprecate');
  // await hetidaDesigner.clickButton('Deprecate workflow');
  await hetidaDesigner.clearTest();
});
