import { expect, test } from '../fixtures/fixture';

test('Open workflow on double-click', async ({ page, hetidaDesigner }) => {
  // Arrange
  const categoryName = 'Examples';
  const workflowName = 'Volatility Detection Example';

  // Act
  await hetidaDesigner.clickWorkflowsInNavigation();
  await hetidaDesigner.clickCategoryInNavigation(categoryName);

  await hetidaDesigner.doubleClickItemInNavigation(categoryName, workflowName);
  await page.waitForSelector('hd-workflow-editor');

  // Assert
  // Check for equal names in list and opened tab
  const workflowListName = await page
    .locator(`mat-expansion-panel:has-text("${categoryName}") >> nth=0`)
    .locator(`.navigation-item:has-text("${workflowName}") >> nth=0`)
    .locator('.text-ellipsis')
    .innerText();
  const workflowTabName = await page
    .locator('div[role="tab"] >> nth=1')
    .locator('.text-ellipsis')
    .innerText();
  expect(workflowListName).toEqual(workflowTabName);

  // Check if hd-workflow-editor exists and contains a svg image
  const svgInEditor = page
    .locator('hd-workflow-editor')
    .locator('svg >> nth=0');
  await expect(svgInEditor).toHaveAttribute('class', 'hetida-flowchart-svg');

  await hetidaDesigner.clearTest();
});
