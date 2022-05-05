import { expect, test } from '../fixtures/fixture';

test('HDOS-379: use a list as fixed any input', async ({
  page,
  hetidaDesigner
}) => {
  // Arrange
  const componentCategoryName = 'Connectors';
  const componentName = 'Pass Through';
  const workflowCategoryName = 'Draft';
  const workflowName = 'Test Workflow HDOS-379';
  const workflowDescription = 'Use a list as fixed any input';
  const workflowImportData = '["hello","world"]';

  // Act
  await hetidaDesigner.clickWorkflowsComponentsInNavigation('Workflows');
  await hetidaDesigner.clickAddWorkflowComponentInNavigation('Add workflow');
  await hetidaDesigner.typeInInput('name', workflowName);
  await hetidaDesigner.typeInInput('description', workflowDescription);
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
  await hetidaDesigner.clickToggleButton(1);
  await hetidaDesigner.clickInput(0);
  await hetidaDesigner.importJson(workflowImportData);
  await hetidaDesigner.clickButton('Save');
  await hetidaDesigner.typeInInputPosition(1, 'Output');
  await hetidaDesigner.clickButton('Save');

  await hetidaDesigner.clickIconInToolbar('Execute');
  await page.waitForSelector('mat-dialog-container');
  await hetidaDesigner.clickButton('Execute');
  await page.waitForSelector('hd-protocol-viewer >> .protocol-content');

  // Assert
  const output = await page
    .locator('hd-protocol-viewer >> .protocol-content >> span >> nth=1')
    .innerText();
  expect(output).toEqual(workflowImportData);

  await hetidaDesigner.clickWorkflowsComponentsInNavigation('Workflows');
  await hetidaDesigner.clickCategoryInNavigation(workflowCategoryName);
  await hetidaDesigner.rightClickItemInNavigation(
    workflowCategoryName,
    workflowName
  );
  await page.locator('.mat-menu-panel').hover();
  await hetidaDesigner.clickOnContextMenu('Delete');
  await hetidaDesigner.clickButton('Delete workflow');
  await hetidaDesigner.clearTest();
});
