import { expect, test } from '../fixtures/fixture';

test('Open "add component" dialog', async ({ page, hetidaDesigner }) => {
  // Arrange
  // Act
  await hetidaDesigner.clickComponentsInNavigation();
  await hetidaDesigner.clickAddButtonInNavigation('Add component');

  // Assert
  const countDialogContainer = await page
    .locator('mat-dialog-container')
    .count();
  expect(countDialogContainer).toEqual(1);

  await hetidaDesigner.clearTest();
});
