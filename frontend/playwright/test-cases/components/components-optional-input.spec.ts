import { expect, test } from '../fixtures/fixture';

test('Create a component with Option Input and Default Value', async ({
  page,
  hetidaDesigner,
  browserName
}) => {
  // Arrange
  const componentCategory = 'Test';
  const componentName = `Test Optional Input component ${browserName}`;
  const componentDescription =
    'Releases a component with Optional Input and Default Value';
  const componentTag = '0.1.0';
  const componentInputName = 'input';
  const componentOutputName = 'output';
  const inputDefaultValue = 'DefaultValueString';
  const inputOptionValue = 'OPTIONAL';

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
  await hetidaDesigner.selectItemInDropdown(
    `${componentInputName}-type-input-component-io-dialog`,
    inputOptionValue
  );
  await hetidaDesigner.typeInInputByTestId(
    `${componentInputName}-optional-input-default-value-component-io-dialog`,
    inputDefaultValue
  );
  await hetidaDesigner.clickByTestId('add-output-component-io-dialog');
  await hetidaDesigner.typeInInputByTestId(
    'new_output_1-label-output-component-io-dialog',
    componentOutputName
  );
  await hetidaDesigner.clickByTestId('save-component-io-dialog');

  // Wait for the store to update
  await page.waitForTimeout(2000);

  // Publish component
  await hetidaDesigner.clickIconInToolbar('Publish');
  await hetidaDesigner.clickByTestId('publish component-confirm-dialog');

  // Get released component I/O
  await hetidaDesigner.clickIconInToolbar('Configure I/O');
  await page.waitForSelector(
    `mat-dialog-container:has-text("Configure Input / Output for Component ${componentName} ${componentTag}")`
  );

  const componentDefaultValueReleased = await page
    .getByTestId(
      `${componentInputName}-optional-input-default-value-component-io-dialog`
    )
    .inputValue();

  await hetidaDesigner.clickByTestId('cancel-component-io-dialog');

  // Assert
  expect(componentDefaultValueReleased).toEqual(inputDefaultValue);
});

test.afterEach(async ({ page, hetidaDesigner, browserName }) => {
  // Clear
  const componentCategory = 'Test';
  const componentName = `Test Optional Input component ${browserName}`;
  const componentTag = '0.1.0';

  await hetidaDesigner.clickComponentsInNavigation();
  await hetidaDesigner.clickCategoryInNavigation(componentCategory);
  await hetidaDesigner.rightClickItemInNavigation(
    componentCategory,
    componentName
  );
  await page.locator('.mat-mdc-menu-panel').hover();
  await hetidaDesigner.clickOnContextMenu('Deprecate');
  await page.waitForSelector(
    `mat-dialog-container:has-text("Deprecate component ${componentName} (${componentTag})")`
  );
  await hetidaDesigner.clickByTestId('deprecate component-confirm-dialog');

  await hetidaDesigner.clearTest();
});
