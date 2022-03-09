import { test, expect } from '../fixtures/fixture';

test('Add workflow, open dialog', async ({
  page,
  hetidaDesigner,
  navigation
}) => {
  // Run test
  await navigation.clickBtnNavigation('Workflows');
  await navigation.clickBtnNavigation('Add workflow');

  // Check if create workflow dialog-container exists
  const countDialogContainer = await page
    .locator('mat-dialog-container')
    .count();
  expect(countDialogContainer).toEqual(1);

  // Run clear
  await hetidaDesigner.clearTest();
});
