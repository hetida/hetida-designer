import { test, expect } from '@playwright/test';
import { HetidaDesigner } from '../page-objects/hetida-designer';
import { Navigation } from '../page-objects/navigation';

test('Open workflow on double-click', async ({ page }) => {
  const hetidaDesigner = new HetidaDesigner(page);
  const navigation = new Navigation(page);

  const categoryName = 'Examples';
  const workflowName = 'Volatility Detection Example';

  // Run setup
  await hetidaDesigner.setupTest();

  // Run test
  await navigation.clickBtnNavigation('workflows');

  // Expansion-panel expands on click
  await navigation.clickExpansionPanelNavigation(categoryName);

  const visibleExpansionPanelContent = page.locator(`mat-expansion-panel:has-text("${categoryName}") >> nth=0`)
    .locator('.mat-expansion-panel-content');

  await expect(visibleExpansionPanelContent).toBeVisible();

  // Open workflow on double-click
  await navigation.doubleClickItemNavigation(categoryName, workflowName);

  // Check for equal names in list and opened tab
  const componentListName = await page.locator(`mat-expansion-panel:has-text("${categoryName}") >> nth=0`)
    .locator(`.navigation-item:has-text("${workflowName}") >> nth=0`)
    .locator('.text-ellipsis').innerText();

  const componentTabName = await page.locator('div[role="tab"] >> nth=1').locator('.text-ellipsis').innerText();
  expect(componentListName).toEqual(componentTabName);

  // Check if hd-workflow-editor exists and contains a svg image
  const svgInEditor = page.locator('hd-workflow-editor').locator('svg >> nth=0');
  await expect(svgInEditor).toHaveAttribute('class', 'hetida-flowchart-svg');

  // Run clear
  await hetidaDesigner.clearTest();
});
