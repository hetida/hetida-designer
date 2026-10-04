import { expect, test } from '../fixtures/fixture';

test('Create a component with Optional Input and Default Value', async ({
  page,
  hetidaDesigner,
  backendApi,
  browserName
}, testInfo) => {
  // Arrange
  const componentCategory = 'Test';
  const componentName = `Test Optional Input component ${browserName} ${testInfo.retry}`;
  const componentDescription =
    'Releases a component with Optional Input and Default Value';
  const componentTag = '0.1.0';
  const componentInputName = 'input';
  const componentOutputName = 'output';
  const inputType = 'OPTIONAL';
  const inputDataType = 'ANY';
  const inputDefaultValue = 'defaultValueString';

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
  await hetidaDesigner.clickIconInToolbar('Configure_IO');
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
    inputType
  );
  await hetidaDesigner.selectItemInDropdown(
    `${componentInputName}-data-type-input-component-io-dialog`,
    inputDataType
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

  // Saving the io dialog is asynchronous, and publishing releases whatever the
  // backend already has - so the inputs and outputs have to have arrived there
  // before going on, or an empty io interface gets released.
  await expect
    .poll(
      async () => {
        const [stub] =
          await backendApi.findTransformationsByName(componentName);
        return stub === undefined
          ? ''
          : `${stub.io_interface.inputs.length}/${stub.io_interface.outputs.length}`;
      },
      { timeout: 15000 }
    )
    .toEqual('1/1');

  // Publish component
  await hetidaDesigner.clickIconInToolbar('Publish');
  await hetidaDesigner.clickByTestId('publish component-confirm-dialog');

  // Get released component I/O
  await hetidaDesigner.clickIconInToolbar('Configure_IO');
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

test.afterEach(
  async ({ page, hetidaDesigner, backendApi, browserName }, testInfo) => {
    // Clear
    const componentCategory = 'Test';
    const componentName = `Test Optional Input component ${browserName} ${testInfo.retry}`;
    const componentTag = '0.1.0';

    // Nothing to remove when the test failed before it created the component.
    // Driving the ui anyway would report a misleading timeout here and hide
    // the actual failure.
    if (
      (await backendApi.findTransformationsByName(componentName)).length === 0
    ) {
      return;
    }

    await hetidaDesigner.clickComponentsInNavigation();
    await hetidaDesigner.searchInNavigation(componentName);
    await hetidaDesigner.clickCategoryInNavigation(componentCategory);
    await hetidaDesigner.rightClickItemInNavigation(
      `${componentName}(${componentTag})`
    );
    await page.locator('.mat-mdc-menu-panel').hover();
    await hetidaDesigner.clickOnContextMenu('Deprecate');
    await page.waitForSelector(
      `mat-dialog-container:has-text("Deprecate component ${componentName} (${componentTag})")`
    );
    await hetidaDesigner.clickByTestId('deprecate component-confirm-dialog');

    await (
      await page.waitForSelector(
        `mat-expansion-panel:has-text("${componentCategory}") >> .navigation-item:has-text("${componentName}")`
      )
    ).waitForElementState('hidden');

    await hetidaDesigner.clearTest();
  }
);

// Runs even when the cleanup above failed, so a leftover can never make the
// next attempt create a second revision with the same name and tag - after
// which every locator for that name matches more than one element.
test.afterEach(async ({ backendApi, browserName }, testInfo) => {
  await backendApi.deleteTransformationsByName(
    `Test Optional Input component ${browserName} ${testInfo.retry}`
  );
});
