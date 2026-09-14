import { expect, test } from '../fixtures/fixture';

// The component is created through the rest api: what is under test is editing
// documentation in the ui, not assembling a component.
test('Edit the documentation of a component in the ui', async ({
  page,
  hetidaDesigner,
  backendApi,
  browserName
}, testInfo) => {
  // Arrange
  const componentCategory = 'Test';
  const componentName = `Test document a component ${browserName} ${testInfo.retry}`;
  const componentTag = '0.1.0';
  const componentDocumentation = `# ${componentName}
## Description
Documents a component
## Inputs
input
## Outputs
output
`;

  const componentId = await backendApi.createComponent({
    name: componentName,
    category: componentCategory,
    description: 'Documents a component',
    versionTag: componentTag,
    inputs: [{ name: 'input', dataType: 'ANY' }],
    outputs: [{ name: 'output', dataType: 'ANY' }],
    functionBody: 'return {"output": input}',
    documentation: ''
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

  await hetidaDesigner.clickIconInToolbar('Open_documentation');
  await page.waitForSelector('hd-documentation-editor >> textarea');
  await hetidaDesigner.typeInDocumentationEditor(componentDocumentation);
  await hetidaDesigner.clickByTestId('save-edit-documentation-editor');

  // Assert
  // Saving is asynchronous, so poll the backend rather than the editor - this
  // checks that the documentation was really persisted, not just displayed.
  await expect
    .poll(
      async () =>
        (await backendApi.getTransformation(componentId)).documentation,
      { timeout: 15000 }
    )
    .toEqual(componentDocumentation);
});

test.afterEach(async ({ backendApi, browserName }, testInfo) => {
  await backendApi.deleteTransformationsByName(
    `Test document a component ${browserName} ${testInfo.retry}`
  );
});
