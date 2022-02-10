import { test, expect } from '@playwright/test';
import { HetidaDesigner } from '../page-objects/hetida-designer';
import { Navigation } from '../page-objects/navigation';

test('Open components on double-click', async ({ page }) => {
  const hetidaDesigner = new HetidaDesigner(page);
  const navigation = new Navigation(page);

  // Run setup
  await hetidaDesigner.setupTest();

  // Run test
  await navigation.clickBtnNavigation('components');

  // Expansion-panel expand
  const panelTitle = 'Basic';
  await navigation.clickExpansionPanelNavigation(panelTitle);
  //await expect(page.locator('mat-expansion-panel-header[role="button"]:has-text("' + panelTitle + '")').first().locator('.mat-expansion-panel-content')).toBeVisible();

  // Component is opening on double-click and loading
  await page.locator('hd-navigation-category').first().locator('.expansion-panel-content').first()
    .locator('.navigation-item').dblclick();

  const componentListTitle = await page.locator('hd-navigation-category').first()
    .locator('.expansion-panel-content').first()
    .locator('.text-ellipsis').innerText();

  const componentTabTitle = await page.locator('div[role="tab"] >> nth=1').locator('.text-ellipsis').innerText();

  // Checking for equal titles in list and opened tab
  expect(componentListTitle).toEqual(componentTabTitle);
  // Checking if hd-component-editor exists
  await expect(page.locator('hd-component-editor').count()).toEqual(1);

  // Run clear
  await hetidaDesigner.clearTest();
});
