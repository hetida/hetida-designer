import { expect, test } from '../fixtures/fixture';

test('Category in workflows expands on click', async ({
  page,
  hetidaDesigner
}) => {
  // Arrange
  const categoryName = 'Examples';

  // Act
  await hetidaDesigner.clickWorkflowsComponentsInNavigation('Workflows');
  await hetidaDesigner.clickCategoryInNavigation(categoryName);

  // Assert
  const expansionPanelContent = page
    .locator(`mat-expansion-panel:has-text("${categoryName}") >> nth=0`)
    .locator('.mat-expansion-panel-content');
  await expect(expansionPanelContent).toBeVisible();

  await hetidaDesigner.clearTest();
});
