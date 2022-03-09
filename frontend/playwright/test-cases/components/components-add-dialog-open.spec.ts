import { test, expect } from '../fixtures/fixture';

test('Add component, open dialog', async ({
  page,
  hetidaDesigner,
  navigation
}) => {
  // Run test
  await navigation.clickBtnNavigation('Components');
  await navigation.clickBtnNavigation('Add component');

  // Check if create component dialog-container exists
  const countDialogContainer = await page
    .locator('mat-dialog-container')
    .count();
  expect(countDialogContainer).toEqual(1);

  // Run clear
  await hetidaDesigner.clearTest();
});
