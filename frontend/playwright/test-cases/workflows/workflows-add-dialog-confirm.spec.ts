import { test, expect } from '@playwright/test';
import { HetidaDesigner } from '../page-objects/hetida-designer';
import { Navigation } from '../page-objects/navigation';

test('Add workflow, type in data and confirm dialog', async ({ page }) => {
  const hetidaDesigner = new HetidaDesigner(page);
  const navigation = new Navigation(page);
  // Test parameter
  const workflowName = 'Factorial';
  const categoryName = 'Draft';
  const shortDescription = 'Calculates my factorial';
  const tag = '1.0.0';

  // Run setup
  await hetidaDesigner.setupTest();

  // Run test
  await navigation.clickBtnNavigation('Workflows');
  await navigation.clickBtnNavigation('Add workflow');

  // Type in workflow details
  await navigation.typeInInputDialog('name', workflowName); // WorkflowName name
  await navigation.typeInInputDialog('category', categoryName); // Category
  await navigation.typeInInputDialog('description', shortDescription); // Short description
  await navigation.typeInInputDialog('tag', tag); // Tag

  // Click on "Create Workflow"
  await navigation.clickBtnDialog('Create Workflow');
  await page.waitForSelector('hd-workflow-editor'); // Wait for hd-workflow-editor

  // Expansion-panel expands on click, to render and locat workflows in list
  await navigation.clickExpansionPanelNavigation(categoryName);

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

  // Run clear
  await hetidaDesigner.clearTest();
});
