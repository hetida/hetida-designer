import { test, expect } from '@playwright/test';
import { HetidaDesigner } from '../page-objects/hetida-designer';
import { Navigation } from '../page-objects/navigation';

test('Search for components', async ({ page }) => {
  const hetidaDesigner = new HetidaDesigner(page);
  const navigation = new Navigation(page);
  // Test parameter
  const categoryName = 'Arithmetic';
  const componentName = 'Pi'; // Search term

  // Run setup
  await hetidaDesigner.setupTest();

  // Run test
  await navigation.clickBtnNavigation('Components');
  // Type in input-search
  await navigation.typeInSearchTerm(componentName);

  // Expansion-panel expands on click, to render and locat components
  await navigation.clickExpansionPanelNavigation(categoryName);

  // Check if components-list is filtered
  const countComponents = await page.locator('hd-navigation-category').count();
  expect(countComponents).toBeGreaterThan(0);

  // Check for equal names in first component found, in list and search term
  const firstComponentListName = await page
    .locator('mat-expansion-panel >> nth=0')
    .locator('.navigation-item >> nth=0')
    .locator('.text-ellipsis')
    .innerText();
  expect(firstComponentListName).toEqual(componentName);

  // Run clear
  await hetidaDesigner.clearTest();
});
