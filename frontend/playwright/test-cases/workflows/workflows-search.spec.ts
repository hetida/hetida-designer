import { expect, test } from '../fixtures/fixture';

test('Search for workflows', async ({ page, hetidaDesigner }) => {
  // Arrange
  const categoryName = 'Examples';
  const workflowName = 'Volatility Detection Example'; // Search term

  // Act
  await hetidaDesigner.clickWorkflowsInNavigation();
  await hetidaDesigner.searchInNavigation(workflowName);
  // Expansion-panel expands on click, to render and locat workflows
  await hetidaDesigner.clickCategoryInNavigation(categoryName);

  // Assert
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

  await hetidaDesigner.clearTest();
});
