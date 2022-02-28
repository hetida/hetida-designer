import { test, expect } from '@playwright/test';
import { HetidaDesigner } from '../page-objects/hetida-designer';
import { Navigation } from '../page-objects/navigation';

test('Expansion-panel expands on click', async ({ page }) => {
  const hetidaDesigner = new HetidaDesigner(page);
  const navigation = new Navigation(page);
  // Test parameter
  const categoryName = 'Arithmetic';

  // Run setup
  await hetidaDesigner.setupTest();

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
