import { expect, test } from '../fixtures/fixture';

test('Confirm release a component', async ({
  page,
  hetidaDesigner,
  browserName
}) => {
  // Arrange
  const componentCategory = 'Test';
  const componentName = `Test release a component ${browserName}`;
  const componentDescription = 'Releases a component';
  const componentTag = '0.1.0';
  const componentInputName = 'input';
  const componentOutputName = 'output';
  const componentInputData = '["MockData1","MockData2"]';
  const componentPythonCode = `return {"${componentOutputName}": ${componentInputName}}`;
  const componentDocumentation = `# ${componentName}
## Description
${componentDescription}
## Inputs
${componentInputName}
## Outputs
${componentOutputName}
## Examples
The json input of a typical call of this component is:
\`\`\`JSON
${componentInputData}
\`\`\`
`;

  // Act
  // Add a new test component
  await hetidaDesigner.clickComponentsInNavigation();
  await hetidaDesigner.clickAddButtonInNavigation('Add component');
  await page.waitForSelector(
    'mat-dialog-container:has-text("Create new component")'
  );
  await hetidaDesigner.typeInInputById('name', componentName);
  await hetidaDesigner.typeInInputById('category', componentCategory);
  await hetidaDesigner.typeInInputById('description', componentDescription);
  await hetidaDesigner.typeInInputById('tag', componentTag);
  await hetidaDesigner.clickByTestId(
    'create component-copy-transformation-dialog'
  );

  // Configure component I/O
  await hetidaDesigner.clickIconInToolbar('Configure I/O');
  await page.waitForSelector(
    `mat-dialog-container:has-text("Configure Input / Output for Component ${componentName} ${componentTag}")`
  );
  await hetidaDesigner.clickByTestId('add-input-component-io-dialog');
  await hetidaDesigner.typeInInputByTestId(
    'new_input_1-label-input-component-io-dialog',
    componentInputName
  );
  await hetidaDesigner.clickByTestId('add-output-component-io-dialog');
  await hetidaDesigner.typeInInputByTestId(
    'new_output_1-label-output-component-io-dialog',
    componentOutputName
  );
  await hetidaDesigner.clickByTestId('save-component-io-dialog');

  // Add component python code and remove "pass"
  await hetidaDesigner.typeInComponentEditor(componentPythonCode, 12);

  // Execute component and get the protocol
  await hetidaDesigner.clickIconInToolbar('Execute');
  await page.waitForSelector(
    `mat-dialog-container:has-text("Execute Component ${componentName} ${componentTag}")`
  );
  await hetidaDesigner.clickByTestId(
    `${componentInputName}-value-input-wiring-dialog`
  );
  await hetidaDesigner.typeInJsonEditor(componentInputData);
  await hetidaDesigner.clickByTestId('save-json-editor');

  // TODO: Wait for a change to happen
  // Wait for the store to update
  await page.waitForTimeout(3000);

  await hetidaDesigner.clickByTestId('execute-wiring-dialog');
  await page.waitForSelector('hd-protocol-viewer >> .protocol-content');
  const outputProtocol = await page
    .locator('hd-protocol-viewer >> .protocol-content >> span >> nth=1')
    .innerText();

  // Add component documentation
  await hetidaDesigner.clickIconInToolbar('Open documentation');
  await page.waitForSelector('hd-documentation-editor >> textarea');
  await hetidaDesigner.typeInDocumentationEditor(componentDocumentation);
  await hetidaDesigner.clickByTestId('save-edit-documentation-editor');

  // Publish component
  await hetidaDesigner.clickTabInNavigation(1);
  await hetidaDesigner.clickIconInToolbar('Publish');
  await hetidaDesigner.clickByTestId('publish component-confirm-dialog');

  // Get released component details
  await hetidaDesigner.clickIconInToolbar('Edit component details');
  await page.waitForSelector(
    `mat-dialog-container:has-text("Edit component ${componentName} ${componentTag}")`
  );
  const componentNameReleased = await page.inputValue('#name');
  const componentCategoryReleased = await page.inputValue('#category');
  const componentDescriptionReleased = await page.inputValue('#description');
  const componentTagReleased = await page.inputValue('#tag');
  await hetidaDesigner.clickByTestId('cancel-copy-transformation-dialog');

  // Get released component I/O
  await hetidaDesigner.clickIconInToolbar('Configure I/O');
  await page.waitForSelector(
    `mat-dialog-container:has-text("Configure Input / Output for Component ${componentName} ${componentTag}")`
  );
  const componentInputReleased = await page
    .getByTestId(`${componentInputName}-label-input-component-io-dialog`)
    .inputValue();
  const componentOutputReleased = await page
    .getByTestId(`${componentOutputName}-label-output-component-io-dialog`)
    .inputValue();
  await hetidaDesigner.clickByTestId('cancel-component-io-dialog');

  // Get released component input data
  await hetidaDesigner.clickIconInToolbar('Execute');
  await page.waitForSelector(
    `mat-dialog-container:has-text("Execute Component ${componentName} ${componentTag}")`
  );
  await hetidaDesigner.clickByTestId(
    `${componentInputName}-value-input-wiring-dialog`
  );
  const componentInputDataReleased = await page
    .locator('hd-json-editor >> .view-lines')
    .innerText();
  await hetidaDesigner.clickByTestId('cancel-json-editor');

  // Get released component protocol
  await hetidaDesigner.clickByTestId('execute-wiring-dialog');
  await page.waitForSelector('hd-protocol-viewer >> .protocol-content');
  const outputProtocolReleased = await page
    .locator('hd-protocol-viewer >> .protocol-content >> span >> nth=1')
    .innerText();

  // Get released component documentation
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
  expect(componentNameReleased).toEqual(componentName);
  expect(componentCategoryReleased).toEqual(componentCategory);
  expect(componentDescriptionReleased).toEqual(componentDescription);
  expect(componentTagReleased).toEqual(componentTag);
  // Configure I/O
  expect(componentInputReleased).toEqual(componentInputName);
  expect(componentOutputReleased).toEqual(componentOutputName);
  // Execute
  expect(componentInputDataReleased).toEqual(componentInputData);
  expect(outputProtocolReleased).toEqual(outputProtocol);
  // Documentation
  expect(workflowDocumentationReleased).toEqual(componentDocumentation);
});

test.afterEach(async ({ page, hetidaDesigner, browserName }) => {
  // Clear
  const componentCategory = 'Test';
  const componentName = `Test release a component ${browserName}`;
  const componentTag = '0.1.0';

  await hetidaDesigner.clickComponentsInNavigation();
  await hetidaDesigner.clickCategoryInNavigation(componentCategory);
  await hetidaDesigner.rightClickItemInNavigation(
    componentCategory,
    componentName
  );
  await page.locator('.mat-mdc-menu-panel').hover();

  if (
    await page
      .locator('.mat-mdc-menu-content >> button:has-text("Deprecate")')
      .isVisible()
  ) {
    await hetidaDesigner.clickOnContextMenu('Deprecate');
    await page.waitForSelector(
      `mat-dialog-container:has-text("Deprecate component ${componentName} (${componentTag})")`
    );
    await hetidaDesigner.clickByTestId('deprecate component-confirm-dialog');
  } else {
    await hetidaDesigner.clickOnContextMenu('Delete');
    await page.waitForSelector(
      `mat-dialog-container:has-text("Delete component ${componentName} (${componentTag})")`
    );
    await hetidaDesigner.clickByTestId('delete component-confirm-dialog');
  }

  await hetidaDesigner.clearTest();
});
