import { expect, test } from '../fixtures/fixture';

test('Category in components expands on click', async ({
  page,
  hetidaDesigner
}) => {
  // Arrange
  const categoryName = 'Arithmetic';

  // Act
  await hetidaDesigner.clickComponentsInNavigation();
  await hetidaDesigner.clickCategoryInNavigation(categoryName);

  // Assert
  const expansionPanelContent = page
    .locator(`mat-expansion-panel:has-text("${categoryName}") >> nth=0`)
    .locator('.mat-expansion-panel-content');
  await expect(expansionPanelContent).toBeVisible();

  await hetidaDesigner.clearTest();
});
