import { test, expect } from '../fixtures/fixture';

test('Expansion-panel in components expands on click', async ({
  page,
  hetidaDesigner,
  navigation
}) => {
  // Test parameter
  const categoryName = 'Arithmetic';

  // Run test
  await navigation.clickBtnNavigation('Components');
  // Click on Expansion-panel
  await navigation.clickExpansionPanelNavigation(categoryName);

  // Expansion-panel expands and content is visible
  const visibleExpansionPanelContent = page
    .locator(`mat-expansion-panel:has-text("${categoryName}") >> nth=0`)
    .locator('.mat-expansion-panel-content');
  await expect(visibleExpansionPanelContent).toBeVisible();

  // Run clear
  await hetidaDesigner.clearTest();
});
