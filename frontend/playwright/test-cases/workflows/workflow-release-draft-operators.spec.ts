import { expect, test } from '../fixtures/fixture';

const category = 'Test';
const versionTag = '0.1.0';

const names = (browserName: string, retry: number) => {
  const suffix = `${browserName} ${retry}`;
  return {
    component: `Test release draft operators component ${suffix}`,
    workflow: `Test release draft operators workflow ${suffix}`
  };
};

// A workflow with DRAFT operators cannot be published. The warning points the
// user to the toolbar button that upgrades the operators and shows its icon, so
// the user does not have to search the toolbar for it.
test('Refuse to publish a workflow with draft operators and show the upgrade button', async ({
  page,
  hetidaDesigner,
  backendApi,
  browserName
}, testInfo) => {
  // Arrange
  const { component, workflow } = names(browserName, testInfo.retry);
  const componentId = await backendApi.createComponent({
    name: component,
    category,
    description: 'Is used as draft operator',
    versionTag,
    inputs: [],
    outputs: [],
    functionBody: 'return {}',
    documentation: ''
  });
  await backendApi.createWorkflow({
    name: workflow,
    category,
    versionTag,
    operatorTransformationIds: [componentId]
  });

  // The navigation is filled on page load.
  await hetidaDesigner.reloadPage();

  // Act
  await hetidaDesigner.clickWorkflowsInNavigation();
  await hetidaDesigner.clickCategoryInNavigation(category);
  await hetidaDesigner.doubleClickItemInNavigation(
    `${workflow}(${versionTag})`
  );
  await hetidaDesigner.clickIconInToolbar('Publish');

  // Assert
  const notification = page.locator('mat-snack-bar-container');
  await expect(notification).toContainText(
    'This workflow contains DRAFT operators and cannot be published.'
  );
  await expect(notification).toContainText(
    '(Upgrade workflow operators) here in the workflow toolbar.'
  );

  const upgradeButtonIcon = await page
    .locator('hd-toolbar mat-icon[data-testid="Upgrade_workflow_operators"]')
    .innerText();
  await expect(notification.locator('mat-icon')).toHaveText(upgradeButtonIcon);

  await expect(
    page.locator('mat-dialog-container'),
    'publish dialog must not open'
  ).toHaveCount(0);

  // Clicking the message closes it before its duration is over.
  await notification.click();
  await expect(notification).toHaveCount(0, { timeout: 2000 });
});

// Cleanup goes through the rest api, see components-release.spec.ts. A
// transformation can only be deleted once no workflow contains it anymore.
test.afterEach(async ({ backendApi, browserName }, testInfo) => {
  const { component, workflow } = names(browserName, testInfo.retry);
  for (const name of [workflow, component]) {
    await backendApi.deleteTransformationsByName(name);
  }
});
