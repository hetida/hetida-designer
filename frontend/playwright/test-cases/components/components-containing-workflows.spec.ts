import { expect, test } from '../fixtures/fixture';

const category = 'Test';
const versionTag = '0.1.0';

const names = (browserName: string, retry: number) => {
  const suffix = `${browserName} ${retry}`;
  return {
    component: `Test containing workflows ${suffix}`,
    inner: `Test containing workflows inner ${suffix}`,
    outer: `Test containing workflows outer ${suffix}`
  };
};

// The properties dialog lists the workflows a transformation is used in,
// directly as operator or nested in another workflow.
test('Show the workflows using a component in its properties dialog', async ({
  page,
  hetidaDesigner,
  backendApi,
  browserName
}, testInfo) => {
  // Arrange
  const { component, inner, outer } = names(browserName, testInfo.retry);
  const componentId = await backendApi.createComponent({
    name: component,
    category,
    description: 'Is used in workflows',
    versionTag,
    inputs: [],
    outputs: [],
    functionBody: 'return {}',
    documentation: ''
  });
  const innerId = await backendApi.createWorkflow({
    name: inner,
    category,
    versionTag,
    operatorTransformationIds: [componentId, componentId]
  });
  await backendApi.createWorkflow({
    name: outer,
    category,
    versionTag,
    operatorTransformationIds: [innerId]
  });

  // The navigation is filled on page load.
  await page.reload({ waitUntil: 'domcontentloaded' });

  // Act
  await hetidaDesigner.clickComponentsInNavigation();
  await hetidaDesigner.clickCategoryInNavigation(category);
  await hetidaDesigner.rightClickItemInNavigation(
    `${component}(${versionTag})`
  );
  await hetidaDesigner.clickOnContextMenu('Properties...');

  // Assert
  const containingWorkflows = page
    .locator('mat-dialog-container')
    .getByTestId('containing-workflows');
  await expect(containingWorkflows).toContainText('Used in 2 workflows:');
  await expect(containingWorkflows.locator('li')).toHaveText([
    `${inner} (${versionTag}), draft — directly as 2 operators`,
    `${outer} (${versionTag}), draft — indirectly via ${inner} (${versionTag})`
  ]);
});

// Cleanup goes through the rest api, see components-release.spec.ts. A
// transformation can only be deleted once no workflow contains it anymore.
test.afterEach(async ({ backendApi, browserName }, testInfo) => {
  const { component, inner, outer } = names(browserName, testInfo.retry);
  for (const name of [outer, inner, component]) {
    await backendApi.deleteTransformationsByName(name);
  }
});
