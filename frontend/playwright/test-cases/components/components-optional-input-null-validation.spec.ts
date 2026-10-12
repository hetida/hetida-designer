import { expect, test } from '../fixtures/fixture';

test('Allow null value as default_value for primitive data types, if the value is optional', async ({
  page,
  hetidaDesigner,
  backendApi,
  browserName
}, testInfo) => {
  // Arrange
  const componentCategory = 'Test';
  const componentName = `Test input optional null value component ${browserName} ${testInfo.retry}`;
  const componentDescription =
    'Allow null value as default_value for primitive data types, if the value is optional';
  const componentTag = '0.1.0';
  const componentInputName = 'input';
  const componentOutputName = 'output';
  const inputType = 'OPTIONAL';
  const inputDataType = 'INT';
  const inputDefaultValue = '1';
  const inputDefaultValueNull = 'null';

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

  // Configure Execute
  await hetidaDesigner.openExecuteDialog(
    `Execute Component ${componentName} ${componentTag}`
  );
  await hetidaDesigner.clickByTestId(
    `${componentInputName}-use-default-input-wiring-dialog`
  );
  await hetidaDesigner.typeInInputByTestId(
    `${componentInputName}-value-input-wiring-dialog`,
    inputDefaultValueNull
  );
  await page
    .getByTestId(`${componentInputName}-value-input-wiring-dialog`)
    .blur();

  const validationError = await page
    .locator('mat-form-field >> mat-error')
    .isVisible();

  // Assert
  expect(validationError).toBeFalsy();
});

test.afterEach(
  async ({ page, hetidaDesigner, backendApi, browserName }, testInfo) => {
    // Clear
    const componentCategory = 'Test';
    const componentName = `Test input optional null value component ${browserName} ${testInfo.retry}`;
    const componentTag = '0.1.0';

    // Nothing to remove when the test failed before it created the component.
    // Driving the ui anyway would report a misleading timeout here and hide
    // the actual failure.
    if (
      (await backendApi.findTransformationsByName(componentName)).length === 0
    ) {
      return;
    }

    await hetidaDesigner.clickByTestId('cancel-wiring-dialog');

    await hetidaDesigner.clickComponentsInNavigation();
    await hetidaDesigner.searchInNavigation(componentName);
    await hetidaDesigner.clickCategoryInNavigation(componentCategory);
    await hetidaDesigner.rightClickItemInNavigation(
      `${componentName}(${componentTag})`
    );
    await page.locator('.mat-mdc-menu-panel').hover();
    await hetidaDesigner.clickOnContextMenu('Delete...');
    await page.waitForSelector(
      `mat-dialog-container:has-text("Delete component ${componentName} (${componentTag})")`
    );
    await hetidaDesigner.clickByTestId('delete component-confirm-dialog');

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
    `Test input optional null value component ${browserName} ${testInfo.retry}`
  );
});
