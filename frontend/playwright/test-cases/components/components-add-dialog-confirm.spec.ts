import { test, expect } from '@playwright/test';
import { HetidaDesigner } from '../page-objects/hetida-designer';
import { Navigation } from '../page-objects/navigation';

test('Add component, type in data and confirm dialog', async ({ page }) => {
  const hetidaDesigner = new HetidaDesigner(page);
  const navigation = new Navigation(page);
  // Test parameter
  const componentName = 'Factorial';
  const categoryName = 'Draft';
  const shortDescription = 'Calculates my factorial';
  const tag = '1.0.0';

  // Run setup
  await hetidaDesigner.setupTest();

  // Run test
  await navigation.clickBtnNavigation('Components');
  await navigation.clickBtnNavigation('Add component');

  // Type in component details
  await navigation.typeInInputDialog('name', componentName); // Component name
  await navigation.typeInInputDialog('category', categoryName); // Category
  await navigation.typeInInputDialog('description', shortDescription); // Short description
  await navigation.typeInInputDialog('tag', tag); // Tag

  // Click on "Create Component"
  await navigation.clickBtnDialog('Create Component');
  await page.waitForSelector('hd-component-editor'); // Wait for hd-component-editor

  // Expansion-panel expands on click, to render and locat components in list
  await navigation.clickExpansionPanelNavigation(categoryName);

  // Check for equal names in list and opened tab
  const componentListName = await page
    .locator(`mat-expansion-panel:has-text("${categoryName}") >> nth=0`)
    .locator(`.navigation-item:has-text("${componentName}") >> nth=0`)
    .locator('.text-ellipsis')
    .innerText();
  const componentTabName = await page
    .locator('div[role="tab"] >> nth=1')
    .locator('.text-ellipsis')
    .innerText();
  expect(componentListName).toEqual(componentTabName);

  // Check if hd-component-editor exists
  const countComponentEditor = await page
    .locator('hd-component-editor')
    .count();
  expect(countComponentEditor).toEqual(1);

  // Run clear
  await hetidaDesigner.clearTest();
});
