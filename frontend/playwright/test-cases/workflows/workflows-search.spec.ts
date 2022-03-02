import { test, expect } from '@playwright/test';
import { HetidaDesigner } from '../page-objects/hetida-designer';
import { Navigation } from '../page-objects/navigation';

test('Search for workflows', async ({ page }) => {
  const hetidaDesigner = new HetidaDesigner(page);
  const navigation = new Navigation(page);
  // Test parameter
  const categoryName = 'Examples';
  const workflowName = 'Volatility Detection Example'; // Search term

  // Run setup
  await hetidaDesigner.setupTest();

  // Run test
  await navigation.clickBtnNavigation('Workflows');
  // Type in input-search
  await navigation.typeInSearchTerm(workflowName);

  // Expansion-panel expands on click, to render and locat workflows
  await navigation.clickExpansionPanelNavigation(categoryName);

  // Check if workflows-list is filtered
  const countWorkflows = await page.locator('hd-navigation-category').count();
  expect(countWorkflows).toBeGreaterThan(0);

  // Check for equal names in first workflow found, in list and search term
  const firstWorkflowListName = await page
    .locator('mat-expansion-panel >> nth=0')
    .locator('.navigation-item >> nth=0')
    .locator('.text-ellipsis')
    .innerText();
  expect(firstWorkflowListName).toEqual(workflowName);

  // Run clear
  await hetidaDesigner.clearTest();
});
