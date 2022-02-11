import { test, expect } from '@playwright/test';
import { HetidaDesigner } from '../page-objects/hetida-designer';
import { Navigation } from '../page-objects/navigation';

test('Open component on double-click', async ({ page }) => {
  const hetidaDesigner = new HetidaDesigner(page);
  const navigation = new Navigation(page);

  const categoryName = 'Basic';
  const componentName = 'Filter';

  // Run setup
  await hetidaDesigner.setupTest();

  // Run test
  await navigation.clickBtnNavigation('components');

  // Expansion-panel expands on click
  await navigation.clickExpansionPanelNavigation(categoryName);

  const visibleExpansionPanelContent = page.locator(`mat-expansion-panel:has-text("${categoryName}") >> nth=0`)
    .locator('.mat-expansion-panel-content');

  await expect(visibleExpansionPanelContent).toBeVisible();

  // Open component on double-click
  await navigation.doubleClickItemNavigation(categoryName, componentName);

  const componentListName = await page.locator(`mat-expansion-panel:has-text("${categoryName}") >> nth=0`)
    .locator(`.navigation-item:has-text("${componentName}") >> nth=0`)
    .locator('.text-ellipsis').innerText();

  const componentTabName = await page.locator('div[role="tab"] >> nth=1').locator('.text-ellipsis').innerText();

  // Check for equal names in list and opened tab
  expect(componentListName).toEqual(componentTabName);
  // Check if hd-component-editor exists
  const countComponentEditor = await page.locator('hd-component-editor').count();
  expect(countComponentEditor).toEqual(1);

  // Run clear
  await hetidaDesigner.clearTest();
});
