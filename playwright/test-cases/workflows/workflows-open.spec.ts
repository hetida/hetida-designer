import { test, expect } from '@playwright/test';
import { HetidaDesignerDevPage } from '../page-objects/hetida-designer-dev-page';

test('workflows opening on double-click', async ({ page }) => {
  // Run setup
  let hetidaDesignerDevPage = new HetidaDesignerDevPage(page);
  await hetidaDesignerDevPage.setupTest();

  // Run test
  await page.locator('button:has-text("workflows")').click();
  await page.waitForSelector('hd-navigation-category'); // Waiting for the workflows-list to finsh loading

  // Expansion-panel is expanding
  await page.locator('hd-navigation-category').first().locator('.mat-expansion-panel-header').click();
  await expect(page.locator('hd-navigation-category').first().locator('.mat-expansion-panel-content')).toBeVisible();

  // Workflow is opening on double-click and loading
  await page.locator('hd-navigation-category').first().locator('.expansion-panel-content').first()
    .locator('.navigation-item').dblclick();

  let workflowListTitle = await page.locator('hd-navigation-category').first()
    .locator('.expansion-panel-content').first()
    .locator('.text-ellipsis').innerText();

  let workflowTabTitle = await page.locator('div[role="tab"] >> nth=1').locator('.text-ellipsis').innerText();

  // Checking for equal titles in list and opened tab
  expect(workflowListTitle).toEqual(workflowTabTitle);
  // Checking if hd-workflow-editor exists and contains a svg image
  await expect(page.locator('hd-workflow-editor').locator('svg >> nth=0')).toHaveAttribute('class', 'hetida-flowchart-svg');

  // Run clear
  await hetidaDesignerDevPage.clearTest();
});
