import { expect, test } from '../fixtures/fixture';

// What is under test is releasing, so the component is created through the rest
// api. Assembling one through the create dialog, the io dialog and the code
// editor first would put a dozen steps in front of the first assertion, none of
// which this test is about - see components-create.spec.ts for those.
test('Releasing a component preserves its definition', async ({
  page,
  hetidaDesigner,
  backendApi,
  browserName
}, testInfo) => {
  // Arrange
  const componentCategory = 'Test';
  const componentName = `Test release a component ${browserName} ${testInfo.retry}`;
  const componentDescription = 'Releases a component';
  const componentTag = '0.1.0';
  const componentInputName = 'input';
  const componentOutputName = 'output';
  const componentInputData = '["MockData1","MockData2"]';
  // The protocol viewer pretty prints the returned value.
  const expectedOutput = '[\n  "MockData1",\n  "MockData2"\n]';
  const componentDocumentation = `# ${componentName}
## Description
${componentDescription}
## Inputs
${componentInputName}
## Outputs
${componentOutputName}
`;

  const componentId = await backendApi.createComponent({
    name: componentName,
    category: componentCategory,
    description: componentDescription,
    versionTag: componentTag,
    inputs: [{ name: componentInputName, dataType: 'ANY' }],
    outputs: [{ name: componentOutputName, dataType: 'ANY' }],
    functionBody: `return {"${componentOutputName}": ${componentInputName}}`,
    documentation: componentDocumentation,
    testWiring: {
      input_wirings: [
        {
          workflow_input_name: componentInputName,
          adapter_id: 'direct_provisioning',
          filters: { value: componentInputData }
        }
      ],
      output_wirings: []
    }
  });

  // The navigation is filled on page load, so it has to be told about the
  // component that was created through the api afterwards.
  await page.reload({ waitUntil: 'domcontentloaded' });

  // Act
  await hetidaDesigner.clickComponentsInNavigation();
  await hetidaDesigner.clickCategoryInNavigation(componentCategory);
  await hetidaDesigner.doubleClickItemInNavigation(
    `${componentName}(${componentTag})`
  );

  await hetidaDesigner.clickIconInToolbar('Publish');
  await hetidaDesigner.clickByTestId('publish component-confirm-dialog');

  // Everything below only means something once the release actually happened.
  await expect
    .poll(async () => (await backendApi.getTransformation(componentId)).state, {
      timeout: 15000
    })
    .toEqual('RELEASED');

  // Assert
  // Soft, so that one aspect that was not preserved does not hide the others.

  // Details
  await hetidaDesigner.clickIconInToolbar('Edit');
  await page.waitForSelector(
    `mat-dialog-container:has-text("Edit component ${componentName} ${componentTag}")`
  );
  expect.soft(await page.inputValue('#name')).toEqual(componentName);
  expect.soft(await page.inputValue('#category')).toEqual(componentCategory);
  expect
    .soft(await page.inputValue('#description'))
    .toEqual(componentDescription);
  expect.soft(await page.inputValue('#tag')).toEqual(componentTag);
  await hetidaDesigner.clickByTestId('cancel-copy-transformation-dialog');

  // Inputs and outputs
  await hetidaDesigner.clickIconInToolbar('Configure_IO');
  await page.waitForSelector(
    `mat-dialog-container:has-text("Configure Input / Output for Component ${componentName} ${componentTag}")`
  );
  expect
    .soft(
      await page
        .getByTestId(`${componentInputName}-label-input-component-io-dialog`)
        .inputValue()
    )
    .toEqual(componentInputName);
  expect
    .soft(
      await page
        .getByTestId(`${componentOutputName}-label-output-component-io-dialog`)
        .inputValue()
    )
    .toEqual(componentOutputName);
  await hetidaDesigner.clickByTestId('cancel-component-io-dialog');

  // Test wiring
  await hetidaDesigner.openExecuteDialog(
    `Execute Component ${componentName} ${componentTag}`
  );
  await hetidaDesigner.clickByTestId(
    `${componentInputName}-value-input-wiring-dialog`
  );
  await page.waitForSelector('hd-json-editor >> .view-lines:has-text("Mock")');
  expect
    .soft(await page.locator('hd-json-editor >> .view-lines').innerText())
    .toEqual(componentInputData);
  await hetidaDesigner.clickByTestId('cancel-json-editor');

  // Code, by way of what it returns
  await hetidaDesigner.clickByTestId('execute-wiring-dialog');
  await page.waitForSelector('hd-protocol-viewer >> .protocol-content');
  await expect
    .soft(
      page.locator('hd-protocol-viewer >> .protocol-content >> span >> nth=1')
    )
    .toHaveText(expectedOutput);

  // Documentation. A released component shows it read only, so there is no
  // textarea to read it back from - check what is rendered, and compare the
  // stored text through the api.
  await hetidaDesigner.clickIconInToolbar('Open_documentation');
  await expect
    .soft(
      page.locator('hd-documentation-editor >> .editor-and-preview__preview')
    )
    .toContainText(componentDescription);
  expect
    .soft((await backendApi.getTransformation(componentId)).documentation)
    .toEqual(componentDocumentation);
});

// Cleanup goes through the rest api: a cleanup that drives the navigation
// menu can hang until the test timeout when it cannot find its target, and
// then leaves the transformation behind for the next attempt. Deleting and
// deprecating from the context menu have their own test.
test.afterEach(async ({ backendApi, browserName }, testInfo) => {
  await backendApi.deleteTransformationsByName(
    `Test release a component ${browserName} ${testInfo.retry}`
  );
});
