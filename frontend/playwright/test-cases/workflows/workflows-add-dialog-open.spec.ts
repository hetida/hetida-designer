import { expect, test } from '../fixtures/fixture';

test('Open "add workflow" dialog', async ({ page, hetidaDesigner }) => {
  // Arrange
  // Act
  await hetidaDesigner.clickWorkflowsComponentsInNavigation('Workflows');
  await hetidaDesigner.clickAddWorkflowComponentInNavigation('Add workflow');

  // Assert
  const countDialogContainer = await page
    .locator('mat-dialog-container')
    .count();
  expect(countDialogContainer).toEqual(1);

  await hetidaDesigner.clearTest();
});
