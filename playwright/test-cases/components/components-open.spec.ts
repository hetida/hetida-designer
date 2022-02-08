import { test, expect } from '@playwright/test';
import { HetidaDesignerDevPage } from '../page-objects/hetida-designer-dev-page';

test('components opening on double-click', async ({ page }) => {
  // Run setup
  let hetidaDesignerDevPage = new HetidaDesignerDevPage(page);
  await hetidaDesignerDevPage.setupTest();

  // Run test
  await page.locator('button:has-text("components")').click();
  await page.waitForSelector('hd-navigation-category'); // Waiting for the components list to finsh loading

  // Expansion-panel is expanding
  await page.locator('hd-navigation-category').first().locator('.mat-expansion-panel-header').click();
  await expect(page.locator('hd-navigation-category').first().locator('.mat-expansion-panel-content')).toBeVisible();

  // Component is opening on double-click and loading
  await page.locator('hd-navigation-category').first().locator('.expansion-panel-content').first()
    .locator('.navigation-item').dblclick();

  let componentListTitle = await page.locator('hd-navigation-category').first()
    .locator('.expansion-panel-content').first()
    .locator('.text-ellipsis').innerText();

  let componentTabTitle = await page.locator('div[role="tab"] >> nth=1').locator('.text-ellipsis').innerText();

  // Checking for equal titles in list and opened tab
  expect(componentListTitle).toEqual(componentTabTitle);
  // Checking if hd-component-editor exists
  expect(await page.locator('hd-component-editor').count()).toEqual(1);

  // Run clear
  await hetidaDesignerDevPage.clearTest();
});
