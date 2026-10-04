import { expect, test } from '../fixtures/fixture';

// Builds a component entirely through the ui - create dialog, io dialog, code
// editor, json editor - and proves the result actually runs. Every other
// component test sets its fixture up through the rest api, so this is the one
// place where the authoring path itself is covered.
test('Create a component in the ui, write its code and execute it', async ({
  page,
  hetidaDesigner,
  backendApi,
  browserName
}, testInfo) => {
  // Arrange
  const componentCategory = 'Test';
  const componentName = `Test create a component ${browserName} ${testInfo.retry}`;
  const componentDescription = 'Creates a component';
  const componentTag = '0.1.0';
  const componentInputName = 'input';
  const componentOutputName = 'output';
  const componentInputData = '["MockData1","MockData2"]';
  const componentPythonCode = `return {"${componentOutputName}": ${componentInputName}}`;
  // The protocol viewer pretty prints the returned value.
  const expectedOutput = '[\n  "MockData1",\n  "MockData2"\n]';

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
  await hetidaDesigner.clickByTestId('add-output-component-io-dialog');
  await hetidaDesigner.typeInInputByTestId(
    'new_output_1-label-output-component-io-dialog',
    componentOutputName
  );
  await hetidaDesigner.clickByTestId('save-component-io-dialog');

  // Configuring inputs and outputs makes the backend regenerate the component
  // code, and the editor reloads it. Typing before that lands is thrown away -
  // silently, because the editor then has nothing to autosave.
  await expect(
    page.locator('hd-component-editor >> .monaco-editor >> .view-lines')
  ).toContainText(`def main(*, ${componentInputName})`);

  // Add component python code, replacing "pass"
  await hetidaDesigner.typeInComponentEditor(componentPythonCode);

  // The editor autosaves on a debounce and executing runs the code stored in
  // the backend, so the code has to have arrived there before going on.
  await expect
    .poll(
      async () => {
        const [stub] =
          await backendApi.findTransformationsByName(componentName);
        return stub === undefined
          ? ''
          : (await backendApi.getTransformation(stub.id)).content;
      },
      { timeout: 15000 }
    )
    .toContain(componentPythonCode);

  // Wire an input value and execute
  await hetidaDesigner.openExecuteDialog(
    `Execute Component ${componentName} ${componentTag}`
  );
  await hetidaDesigner.clickByTestId(
    `${componentInputName}-value-input-wiring-dialog`
  );
  await hetidaDesigner.typeInJsonEditor(componentInputData, browserName);
  await hetidaDesigner.clickByTestId('save-json-editor');

  // The json editor writes its content back into the wiring form
  // asynchronously. Executing before that lands would send an empty value.
  await expect(
    page.getByTestId(`${componentInputName}-value-input-wiring-dialog`)
  ).toHaveValue(componentInputData, { timeout: 15000 });

  await hetidaDesigner.clickByTestId('execute-wiring-dialog');
  await page.waitForSelector('hd-protocol-viewer >> .protocol-content');

  // Assert
  // The component assembled in the ui runs and returns its input unchanged.
  await expect(
    page.locator('hd-protocol-viewer >> .protocol-content >> span >> nth=1')
  ).toHaveText(expectedOutput);
});

// Cleanup goes through the rest api: a cleanup that drives the navigation
// menu can hang until the test timeout when it cannot find its target, and
// then leaves the transformation behind for the next attempt. Deleting and
// deprecating from the context menu have their own test.
test.afterEach(async ({ backendApi, browserName }, testInfo) => {
  await backendApi.deleteTransformationsByName(
    `Test create a component ${browserName} ${testInfo.retry}`
  );
});
