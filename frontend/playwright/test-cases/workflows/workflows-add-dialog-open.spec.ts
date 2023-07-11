import { expect, test } from '../fixtures/fixture';

test('Open "add workflow" dialog', async ({ page, hetidaDesigner }) => {
  // Arrange
  // Act
  await hetidaDesigner.clickWorkflowsInNavigation();
  await hetidaDesigner.clickAddButtonInNavigation('Add workflow');

  // Assert
  const countDialogContainer = await page
    .locator('mat-dialog-container')
    .count();
  expect(countDialogContainer).toEqual(1);

  await hetidaDesigner.clearTest();
});
