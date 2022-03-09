import { test, expect } from '../fixtures/fixture';

test.describe(
  'Create a "factorial" component and use it, in a new created workflow',
  () => {
    test.afterEach(async ({ hetidaDesigner }) => {
      // Run clear
      await hetidaDesigner.clearTest();
    });

    test('Add component, type in data and confirm dialog', async ({
      page,
      navigation
    }) => {
      // Test parameter
      const componentName = 'Factorial';
      const categoryName = 'Draft';
      const shortDescription = 'Calculates my factorial';
      const tag = '1.0.0';

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
    });

    test('Component "factorial" set inputs and outputs', async ({
      navigation
    }) => {
      // Test parameter
      const componentName = 'Factorial';
      const categoryName = 'Draft';
      const inputs = { label: 'data', type: 'INT' };
      const outputs = { label: 'factorial', type: 'INT' };

      // Run test
      await navigation.clickBtnNavigation('Components');
      await navigation.clickExpansionPanelNavigation(categoryName);
      await navigation.doubleClickItemNavigation(categoryName, componentName);
      // Set inputs and outputs
      await navigation.clickIconToolbar('Configure I/O');

      await navigation.typeInInputDialog('mat-input-13', inputs.label);
      // await navigation.clickBtnDialog('Save');
    });

    test('Add workflow, type in data and confirm dialog', async ({
      page,
      navigation
    }) => {
      // Test parameter
      const workflowName = 'Factorial';
      const categoryName = 'Draft';
      const shortDescription = 'Calculates my factorial';
      const tag = '1.0.0';

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
      await expect(svgInEditor).toHaveAttribute(
        'class',
        'hetida-flowchart-svg'
      );
    });

    test('Delete workflow on right-click via context-menu, dialog open', async ({
      page,
      navigation
    }) => {
      // Test parameter
      const categoryName = 'Draft';
      const componentName = 'Factorial';

      // Run test
      await navigation.clickBtnNavigation('Workflows');
      await navigation.clickExpansionPanelNavigation(categoryName);
      // Open context-menu via right-click on a workflow
      await navigation.rightClickItemNavigation(categoryName, componentName);

      // !!! Fix hover over context-menu (DELETE LATER) !!!
      await page.locator('.mat-menu-content >> Button >> nth=0').hover(); // !!! DELETE !!!

      // Delete workflow on right-click via context-menu
      await navigation.clickContextMenu('Delete');

      // Check if delete workflow dialog-container exists
      const countDialogContainer = await page
        .locator('mat-dialog-container')
        .count();
      expect(countDialogContainer).toEqual(1);
    });

    test('Delete workflow on right-click via context-menu and confirm dialog', async ({
      page,
      navigation
    }) => {
      // Test parameter
      const categoryName = 'Draft';
      const workflowName = 'Factorial';

      // Run test
      await navigation.clickBtnNavigation('Workflows');
      await navigation.clickExpansionPanelNavigation(categoryName);
      // Open context-menu via right-click on a workflow
      await navigation.rightClickItemNavigation(categoryName, workflowName);

      // !!! Fix hover over context-menu (DELETE LATER) !!!
      await page.locator('.mat-menu-content >> Button >> nth=0').hover(); // !!! DELETE !!!

      // Delete workflow on right-click via context-menu
      await navigation.clickContextMenu('Delete');

      // Confirm dialog
      await navigation.clickBtnDialog('Delete workflow');

      // Check if workflow was deleted
      await navigation.typeInSearchTerm(workflowName);

      const searchResult = page.locator('.navigation-container__scrollable');
      await expect(searchResult).toBeEmpty();
    });

    test('Delete component on right-click via context-menu, dialog open', async ({
      page,
      navigation
    }) => {
      // Test parameter
      const categoryName = 'Draft';
      const componentName = 'Factorial';

      // Run test
      await navigation.clickBtnNavigation('Components');
      await navigation.clickExpansionPanelNavigation(categoryName);
      // Open context-menu via right-click on a component
      await navigation.rightClickItemNavigation(categoryName, componentName);

      // !!! Fix hover over context-menu (DELETE LATER) !!!
      await page.locator('.mat-menu-content >> Button >> nth=0').hover(); // !!! DELETE !!!

      // Delete component on right-click via context-menu
      await navigation.clickContextMenu('Delete');

      // Check if delete component dialog-container exists
      const countDialogContainer = await page
        .locator('mat-dialog-container')
        .count();
      expect(countDialogContainer).toEqual(1);
    });

    test('Delete component on right-click via context-menu and confirm dialog', async ({
      page,
      navigation
    }) => {
      // Test parameter
      const categoryName = 'Draft';
      const componentName = 'Factorial';

      // Run test
      await navigation.clickBtnNavigation('Components');
      await navigation.clickExpansionPanelNavigation(categoryName);
      // Open context-menu via right-click on a component
      await navigation.rightClickItemNavigation(categoryName, componentName);

      // !!! Fix hover over context-menu (DELETE LATER) !!!
      await page.locator('.mat-menu-content >> Button >> nth=0').hover(); // !!! DELETE !!!

      // Delete component on right-click via context-menu
      await navigation.clickContextMenu('Delete');

      // Confirm dialog
      await navigation.clickBtnDialog('Delete component');

      // Check if component was deleted
      await navigation.typeInSearchTerm(componentName);

      const searchResult = page.locator('.navigation-container__scrollable');
      await expect(searchResult).toBeEmpty();
    });
  }
);
