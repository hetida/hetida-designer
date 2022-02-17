import { test, expect } from '@playwright/test';
import { HetidaDesigner } from '../page-objects/hetida-designer';
import { Navigation } from '../page-objects/navigation';
import { ErrorNotification } from '../page-objects/error-notification';

test('Open component on double-click', async ({ page }) => {
  const hetidaDesigner = new HetidaDesigner(page);
  const navigation = new Navigation(page);
  const errorNotification = new ErrorNotification(page);

  const categoryName = 'Arithmetic';
  const componentName = 'Pi';

  // Run setup
  await hetidaDesigner.setupTest();

  // Run test
  await navigation.clickBtnNavigation('components');

  // Expansion-panel expands on click
  await navigation.clickExpansionPanelNavigation(categoryName);

  const visibleExpansionPanelContent = page
    .locator(`mat-expansion-panel:has-text("${categoryName}") >> nth=0`)
    .locator('.mat-expansion-panel-content');
  await expect(visibleExpansionPanelContent).toBeVisible();

  // Hover over component, check if error-notification occurred
  await navigation.hoverItemNavigation(categoryName, componentName);
  await errorNotification.checkErrorNotification();

  // Open component on double-click
  await navigation.doubleClickItemNavigation(categoryName, componentName);

  // Check for equal names in list and opened tab
  const componentListName = await page
    .locator(`mat-expansion-panel:has-text("${categoryName}") >> nth=0`)
    .locator(`.navigation-item:has-text("${componentName}") >> nth=0`)
    .locator('.text-ellipsis')
    .innerText();
  const componentTabName = await page
    .locator('div[role="tab"] >> nth=1')
    .locator('.text-ellipsis')
    .innerText();
  expect(componentListName).toEqual(componentTabName);

  // Check if hd-component-editor exists
  const countComponentEditor = await page
    .locator('hd-component-editor')
    .count();
  expect(countComponentEditor).toEqual(1);

  // Run clear
  await hetidaDesigner.clearTest();
});
