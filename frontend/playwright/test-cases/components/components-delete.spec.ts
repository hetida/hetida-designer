import { expect, test } from '../fixtures/fixture';

// Deleting and deprecating from the context menu used to be covered only as a
// side effect of the afterEach hooks that cleaned other tests up. That made
// them assert nothing, and a cleanup that could not find its target burned the
// whole test timeout and left the transformation behind for the next attempt.
// Cleanup is done through the rest api now, so these two actions need tests.

const componentCategory = 'Test';
const componentTag = '0.1.0';

const componentDefinition = (name: string) => ({
  name,
  category: componentCategory,
  description: 'Context menu actions',
  versionTag: componentTag,
  inputs: [{ name: 'input', dataType: 'ANY' }],
  outputs: [{ name: 'output', dataType: 'ANY' }],
  functionBody: 'return {"output": input}',
  documentation: ''
});

test('Delete a draft component from the context menu', async ({
  page,
  hetidaDesigner,
  backendApi,
  browserName
}, testInfo) => {
  // Arrange
  const componentName = `Test delete a component ${browserName} ${testInfo.retry}`;
  await backendApi.createComponent(componentDefinition(componentName));

  // The navigation is filled on page load, so it has to be told about the
  // component that was created through the api afterwards.
  await page.reload({ waitUntil: 'domcontentloaded' });

  // Act
  await hetidaDesigner.clickComponentsInNavigation();
  await hetidaDesigner.searchInNavigation(componentName);
  await hetidaDesigner.clickCategoryInNavigation(componentCategory);
  await hetidaDesigner.rightClickItemInNavigation(
    `${componentName}(${componentTag})`
  );
  await page.locator('.mat-mdc-menu-panel').hover();
  await hetidaDesigner.clickOnContextMenu('Delete');
  await page.waitForSelector(
    `mat-dialog-container:has-text("Delete component ${componentName} (${componentTag})")`
  );
  await hetidaDesigner.clickByTestId('delete component-confirm-dialog');

  // Assert
  // Gone from the navigation ...
  await expect(
    page.getByTestId(
      `${componentName.toLowerCase()}(${componentTag})-navigation-item`
    )
  ).toHaveCount(0);
  // ... and really deleted, not just hidden.
  await expect
    .poll(
      async () =>
        (await backendApi.findTransformationsByName(componentName)).length,
      { timeout: 15000 }
    )
    .toEqual(0);
});

test('Deprecate a released component from the context menu', async ({
  page,
  hetidaDesigner,
  backendApi,
  browserName
}, testInfo) => {
  // Arrange
  const componentName = `Test deprecate a component ${browserName} ${testInfo.retry}`;
  const componentId = await backendApi.createComponent(
    componentDefinition(componentName)
  );
  await backendApi.releaseComponent(componentId);

  await page.reload({ waitUntil: 'domcontentloaded' });

  // Act
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

  // Assert
  // A deprecated component is disabled rather than removed, and the navigation
  // stops offering it.
  await expect
    .poll(async () => (await backendApi.getTransformation(componentId)).state, {
      timeout: 15000
    })
    .toEqual('DISABLED');
  await expect(
    page.getByTestId(
      `${componentName.toLowerCase()}(${componentTag})-navigation-item`
    )
  ).toHaveCount(0);
});

test.afterEach(async ({ backendApi, browserName }, testInfo) => {
  for (const base of [
    'Test delete a component',
    'Test deprecate a component'
  ]) {
    await backendApi.deleteTransformationsByName(
      `${base} ${browserName} ${testInfo.retry}`
    );
  }
});
