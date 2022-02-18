import { test, expect } from '@playwright/test';
import { HetidaDesigner } from '../page-objects/hetida-designer';
import { Navigation } from '../page-objects/navigation';

test('Search for components', async ({ page }) => {
  const hetidaDesigner = new HetidaDesigner(page);
  const navigation = new Navigation(page);

  const categoryName = 'Arithmetic';
  const componentName = 'Pi'; // Search term

  // Run setup
  await hetidaDesigner.setupTest();

  // Run test
  await navigation.clickBtnNavigation('components');

  // Check for loaded components
  let countComponents = await page.locator('hd-navigation-category').count();
  expect(countComponents).toBeGreaterThan(0);

  // Click and type, in input-search
  await navigation.clickInputSearch();
  await navigation.typeInSearchTerm(componentName);

  // Check if components-list is filtered
  countComponents = await page.locator('hd-navigation-category').count();
  expect(countComponents).toBeGreaterThan(0);

  // Expansion-panel expands on click, only for better view on screenshot
  await navigation.clickExpansionPanelNavigation(categoryName);

  // Check for equal names in first component, found in list and search term
  const firstComponentListName = await page
    .locator('mat-expansion-panel >> nth=0')
    .locator('.navigation-item >> nth=0')
    .locator('.text-ellipsis')
    .innerText();
  expect(firstComponentListName).toEqual(componentName);

  // Run clear
  await hetidaDesigner.clearTest();
});
