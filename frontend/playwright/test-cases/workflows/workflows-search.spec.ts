import { test, expect } from '@playwright/test';
import { HetidaDesigner } from '../page-objects/hetida-designer';
import { Navigation } from '../page-objects/navigation';

test('Search for workflows', async ({ page }) => {
  const hetidaDesigner = new HetidaDesigner(page);
  const navigation = new Navigation(page);

  const categoryName = 'Examples';
  const workflowName = 'Volatility Detection Example'; // Search term

  // Run setup
  await hetidaDesigner.setupTest();

  // Run test
  await navigation.clickBtnNavigation('workflows');

  // Check for loaded workflows
  let countWorkflows = await page.locator('hd-navigation-category').count();
  expect(countWorkflows).toBeGreaterThan(0);

  // Click and type, in input-search
  await navigation.clickInputSearch();
  await navigation.typeInSearchTerm(workflowName);

  // Check if workflows-list is filtered
  countWorkflows = await page.locator('hd-navigation-category').count();
  expect(countWorkflows).toBeGreaterThan(0);

  // Expansion-panel expands on click, only for better view on screenshot
  await navigation.clickExpansionPanelNavigation(categoryName);

  // Check for equal names in first workflow, found in list and search term
  const firstWorkflowListName = await page
    .locator('mat-expansion-panel >> nth=0')
    .locator('.navigation-item >> nth=0')
    .locator('.text-ellipsis')
    .innerText();
  expect(firstWorkflowListName).toEqual(workflowName);

  // Run clear
  await hetidaDesigner.clearTest();
});
