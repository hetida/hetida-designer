import { BackendApi } from '../fixtures/backend-api';
import { expect, test } from '../fixtures/fixture';

const componentCategory = 'Test';
const componentTag = '0.1.0';
const inputName = 'input';
const outputName = 'output';
const releaseValue = 'release value';
const changedValue = 'changed value';

const wiringWithValue = (value: string) => ({
  input_wirings: [
    {
      workflow_input_name: inputName,
      adapter_id: 'direct_provisioning',
      filters: { value }
    }
  ],
  output_wirings: [] as unknown[]
});

// Releasing stores the test wiring as release wiring - releasing has its own
// test, so it happens through the rest api here.
const createReleasedComponent = async (
  backendApi: BackendApi,
  componentName: string
): Promise<string> => {
  const componentId = await backendApi.createComponent({
    name: componentName,
    category: componentCategory,
    description: 'Resets to its release wiring',
    versionTag: componentTag,
    inputs: [{ name: inputName, dataType: 'STRING' }],
    outputs: [{ name: outputName, dataType: 'STRING' }],
    functionBody: `return {"${outputName}": ${inputName}}`,
    documentation: '',
    testWiring: wiringWithValue(releaseValue)
  });
  await backendApi.releaseComponent(componentId);
  return componentId;
};

// The test wiring of a released component may still change, so the wiring
// dialog offers to go back to the release wiring.
test('Reset the test wiring of a released component to its release wiring', async ({
  page,
  hetidaDesigner,
  backendApi,
  browserName
}, testInfo) => {
  // Arrange
  const componentName = `Test reset to release wiring ${browserName} ${testInfo.retry}`;
  const componentId = await createReleasedComponent(backendApi, componentName);
  await backendApi.updateTestWiring(componentId, wiringWithValue(changedValue));

  // The navigation is filled on page load, so it has to be told about the
  // component that was created through the api afterwards.
  await page.reload({ waitUntil: 'domcontentloaded' });

  await hetidaDesigner.clickComponentsInNavigation();
  await hetidaDesigner.clickCategoryInNavigation(componentCategory);
  await hetidaDesigner.doubleClickItemInNavigation(
    `${componentName}(${componentTag})`
  );
  await hetidaDesigner.openExecuteDialog(
    `Execute Component ${componentName} ${componentTag}`
  );

  const valueInput = page.getByTestId(`${inputName}-value-input-wiring-dialog`);
  await expect(valueInput).toHaveValue(changedValue);

  // Act
  await hetidaDesigner.clickByTestId('reset-to-release-wiring-wiring-dialog');

  // Assert
  await expect(valueInput).toHaveValue(releaseValue);

  // Only confirming the dialog stores the wiring as test wiring.
  await hetidaDesigner.clickByTestId('execute-wiring-dialog');
  await expect
    .poll(
      async () => (await backendApi.getTransformation(componentId)).test_wiring,
      { timeout: 15000 }
    )
    .toMatchObject(wiringWithValue(releaseValue));
  await expect(
    page.locator('hd-protocol-viewer >> .protocol-content')
  ).toContainText(releaseValue);
});

// The wiring dialog of a schedule offers the same reset, to the release wiring
// of the scheduled component.
test('Reset the wiring of a schedule to the release wiring of its component', async ({
  page,
  hetidaDesigner,
  backendApi,
  browserName
}, testInfo) => {
  // Arrange
  const componentName = `Test reset schedule to release wiring ${browserName} ${testInfo.retry}`;
  const componentId = await createReleasedComponent(backendApi, componentName);
  const scheduleId = await backendApi.createSchedule(
    componentName,
    componentId,
    wiringWithValue(changedValue)
  );

  // Schedules and the navigation are loaded on page load.
  await page.reload({ waitUntil: 'domcontentloaded' });

  await hetidaDesigner.clickTabInNavigation(1);
  await page
    .locator('.scheduling-row', { hasText: componentName })
    .getByRole('button', { name: 'Edit Wiring' })
    .click();
  await expect(
    page.locator(
      `mat-dialog-container:has-text("Change Wiring — ${componentName} ${componentTag}")`
    )
  ).toBeVisible();

  const valueInput = page.getByTestId(`${inputName}-value-input-wiring-dialog`);
  await expect(valueInput).toHaveValue(changedValue);

  // Act
  await hetidaDesigner.clickByTestId('reset-to-release-wiring-wiring-dialog');

  // Assert
  await expect(valueInput).toHaveValue(releaseValue);

  // Only confirming the dialog stores the wiring of the schedule.
  await hetidaDesigner.clickByTestId('save wiring-wiring-dialog');
  await expect
    .poll(async () => (await backendApi.getSchedule(scheduleId)).wiring, {
      timeout: 15000
    })
    .toMatchObject(wiringWithValue(releaseValue));
});

// Cleanup goes through the rest api, see components-release.spec.ts.
test.afterEach(async ({ backendApi, browserName }, testInfo) => {
  for (const name of [
    `Test reset to release wiring ${browserName} ${testInfo.retry}`,
    `Test reset schedule to release wiring ${browserName} ${testInfo.retry}`
  ]) {
    await backendApi.deleteSchedulesByName(name);
    await backendApi.deleteTransformationsByName(name);
  }
});
