import { test, expect } from '@playwright/test';
import { HetidaDesigner } from '../page-objects/hetida-designer';
import { Navigation } from '../page-objects/navigation';

test('Open workflows on double-click', async ({ page }) => {
  const hetidaDesigner = new HetidaDesigner(page);
  const navigation = new Navigation(page);

  // Run setup
  await hetidaDesigner.setupTest();

  // Run test
  await navigation.clickBtnNavigation('workflows');

  // Expansion-panel is expanding
  await page.locator('hd-navigation-category').first().locator('.mat-expansion-panel-header').click();
  await expect(page.locator('hd-navigation-category').first().locator('.mat-expansion-panel-content')).toBeVisible();

  // Workflow is opening on double-click and loading
  await page.locator('hd-navigation-category').first().locator('.expansion-panel-content').first()
    .locator('.navigation-item').dblclick();

  const workflowListTitle = await page.locator('hd-navigation-category').first()
    .locator('.expansion-panel-content').first()
    .locator('.text-ellipsis').innerText();

  const workflowTabTitle = await page.locator('div[role="tab"] >> nth=1').locator('.text-ellipsis').innerText();

  // Checking for equal titles in list and opened tab
  expect(workflowListTitle).toEqual(workflowTabTitle);
  // Checking if hd-workflow-editor exists and contains a svg image
  await expect(page.locator('hd-workflow-edito').locator('svg >> nth=0')).toHaveAttribute('class', 'hetida-flowchart-svg');

  // Run clear
  await hetidaDesigner.clearTest();
});
