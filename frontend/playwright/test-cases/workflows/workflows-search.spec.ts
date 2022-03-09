import { test, expect } from '../fixtures/fixture';

test('Search for workflows', async ({ page, hetidaDesigner, navigation }) => {
  // Test parameter
  const categoryName = 'Examples';
  const workflowName = 'Volatility Detection Example'; // Search term

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
