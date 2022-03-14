import { test, expect } from '../fixtures/fixture';

test('Category in components expands on click', async ({
  page,
  hetidaDesigner
}) => {
  // Arrange
  const categoryName = 'Arithmetic';

  // Act
  await hetidaDesigner.clickWorkflowsComponentsInNavigation('Components');
  await hetidaDesigner.clickCategoryInNavigation(categoryName);

  // Assert
  const visibleExpansionPanelContent = page
    .locator(`mat-expansion-panel:has-text("${categoryName}") >> nth=0`)
    .locator('.mat-expansion-panel-content');
  await expect(visibleExpansionPanelContent).toBeVisible();

  // Run clear
  await hetidaDesigner.clearTest();
});
