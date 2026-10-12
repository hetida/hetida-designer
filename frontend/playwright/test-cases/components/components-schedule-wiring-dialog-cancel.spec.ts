import { expect, test } from '../fixtures/fixture';

// All wiring dialogs share one config, and the one of a schedule changes the
// text of its confirm button. Cancelling it used to leave that text behind, so
// that every execute dialog afterwards offered "Save Wiring" instead.
test('Cancelling the wiring dialog of a schedule leaves the execute dialog unchanged', async ({
  page,
  hetidaDesigner,
  backendApi,
  browserName
}, testInfo) => {
  // Arrange
  const componentCategory = 'Test';
  const componentName = `Test cancel schedule wiring ${browserName} ${testInfo.retry}`;
  const componentTag = '0.1.0';

  const componentId = await backendApi.createComponent({
    name: componentName,
    category: componentCategory,
    description: 'Is scheduled',
    versionTag: componentTag,
    inputs: [],
    // A component without any io is incomplete and cannot be executed.
    outputs: [{ name: 'output', dataType: 'INT' }],
    functionBody: 'return {"output": 1}',
    documentation: ''
  });
  await backendApi.createSchedule(componentName, componentId, {
    input_wirings: [],
    output_wirings: []
  });

  // Schedules and the navigation are loaded on page load.
  await page.reload({ waitUntil: 'domcontentloaded' });

  // Act
  await hetidaDesigner.clickTabInNavigation(1);
  await page
    .locator('.scheduling-row', { hasText: componentName })
    .getByRole('button', { name: 'Edit Wiring' })
    .click();
  await hetidaDesigner.clickByTestId('cancel-wiring-dialog');
  await expect(page.locator('mat-dialog-container')).toHaveCount(0);

  await hetidaDesigner.clickComponentsInNavigation();
  await hetidaDesigner.clickCategoryInNavigation(componentCategory);
  await hetidaDesigner.doubleClickItemInNavigation(
    `${componentName}(${componentTag})`
  );
  await hetidaDesigner.openExecuteDialog(
    `Execute Component ${componentName} ${componentTag}`
  );

  // Assert
  await expect(page.getByTestId('execute-wiring-dialog')).toHaveText('Execute');
});

// Cleanup goes through the rest api, see components-release.spec.ts.
test.afterEach(async ({ backendApi, browserName }, testInfo) => {
  const name = `Test cancel schedule wiring ${browserName} ${testInfo.retry}`;
  await backendApi.deleteSchedulesByName(name);
  await backendApi.deleteTransformationsByName(name);
});
