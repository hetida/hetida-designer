import { test, expect } from '../fixtures/fixture';

test('Add component, open dialog', async ({ page, hetidaDesigner }) => {
  // Arrange
  // Act
  await hetidaDesigner.clickWorkflowsComponentsInNavigation('Components');
  await hetidaDesigner.clickAddWorkflowComponentInNavigation('Add component');

  // Assert
  const countDialogContainer = await page
    .locator('mat-dialog-container')
    .count();
  expect(countDialogContainer).toEqual(1);

  // Run clear
  await hetidaDesigner.clearTest();
});
