import { test, expect } from '../fixtures/fixture';

test.describe(
  'Create a "factorial" component and use it, in a new created workflow',
  () => {
    test('Add component, type in data and confirm dialog', async ({
      page,
      hetidaDesigner
    }) => {
      // Arrange
      const componentName = 'Factorial';
      const categoryName = 'Draft';
      const shortDescription = 'Calculates my factorial';
      const tag = '1.0.0';

      // Act
      await hetidaDesigner.clickWorkflowsComponentsInNavigation('Components');
      await hetidaDesigner.clickAddWorkflowComponentInNavigation(
        'Add component'
      );

      // Type in component details
      await hetidaDesigner.typeInAnyInputInDialog('name', componentName); // Component name
      await hetidaDesigner.typeInAnyInputInDialog('category', categoryName); // Category
      await hetidaDesigner.typeInAnyInputInDialog(
        'description',
        shortDescription
      ); // Short description
      await hetidaDesigner.typeInAnyInputInDialog('tag', tag); // Tag

      await hetidaDesigner.clickAnyBtnInDialog('Create Component');
      await page.waitForSelector('hd-component-editor');

      // Category expands on click, to render and locat components in list
      await hetidaDesigner.clickCategoryInNavigation(categoryName);

      // Assert
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

      const countComponentEditor = await page
        .locator('hd-component-editor')
        .count();
      expect(countComponentEditor).toEqual(1);
    });

    test('Component "factorial" set inputs and outputs', async ({
      hetidaDesigner
    }) => {
      // Arrange
      const componentName = 'Factorial';
      const categoryName = 'Draft';
      const inputs = { label: 'data', type: 'INT' };
      const outputs = { label: 'factorial', type: 'INT' };

      // Act
      await hetidaDesigner.clickWorkflowsComponentsInNavigation('Components');
      await hetidaDesigner.clickCategoryInNavigation(categoryName);
      await hetidaDesigner.doubleClickItemInNavigation(
        categoryName,
        componentName
      );
      // Set inputs and outputs
      await hetidaDesigner.clickIconInToolbar('Configure I/O');
      await hetidaDesigner.typeInAnyInputInDialog('mat-input-13', inputs.label);
      // await hetidaDesigner.clickBtnDialog('Save');

      // Assert
    });

    test('Add workflow, type in data and confirm dialog', async ({
      page,
      hetidaDesigner
    }) => {
      // Arrange
      const workflowName = 'Factorial';
      const categoryName = 'Draft';
      const shortDescription = 'Calculates my factorial';
      const tag = '1.0.0';

      // Act
      await hetidaDesigner.clickWorkflowsComponentsInNavigation('Workflows');
      await hetidaDesigner.clickAddWorkflowComponentInNavigation(
        'Add workflow'
      );

      // Type in workflow details
      await hetidaDesigner.typeInAnyInputInDialog('name', workflowName); // WorkflowName name
      await hetidaDesigner.typeInAnyInputInDialog('category', categoryName); // Category
      await hetidaDesigner.typeInAnyInputInDialog(
        'description',
        shortDescription
      ); // Short description
      await hetidaDesigner.typeInAnyInputInDialog('tag', tag); // Tag

      await hetidaDesigner.clickAnyBtnInDialog('Create Workflow');
      await page.waitForSelector('hd-workflow-editor');

      // Category expands on click, to render and locat workflows in list
      await hetidaDesigner.clickCategoryInNavigation(categoryName);

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
      await expect(svgInEditor).toHaveAttribute(
        'class',
        'hetida-flowchart-svg'
      );
    });

    test('Delete workflow on right-click via context-menu, dialog open', async ({
      page,
      hetidaDesigner
    }) => {
      // Arrange
      const categoryName = 'Draft';
      const componentName = 'Factorial';

      // Act
      await hetidaDesigner.clickWorkflowsComponentsInNavigation('Workflows');
      await hetidaDesigner.clickCategoryInNavigation(categoryName);
      // Open context-menu via right-click on a workflow
      await hetidaDesigner.rightClickItemInNavigation(
        categoryName,
        componentName
      );

      // !!! Fix hover over context-menu (DELETE LATER) !!!
      await page.locator('.mat-menu-content >> Button >> nth=0').hover();

      await hetidaDesigner.clickOnContextMenu('Delete');

      // Assert
      const countDialogContainer = await page
        .locator('mat-dialog-container')
        .count();
      expect(countDialogContainer).toEqual(1);
    });

    test('Delete workflow on right-click via context-menu and confirm dialog', async ({
      page,
      hetidaDesigner
    }) => {
      // Arrange
      const categoryName = 'Draft';
      const workflowName = 'Factorial';

      // Act
      await hetidaDesigner.clickWorkflowsComponentsInNavigation('Workflows');
      await hetidaDesigner.clickCategoryInNavigation(categoryName);
      // Open context-menu via right-click on a workflow
      await hetidaDesigner.rightClickItemInNavigation(
        categoryName,
        workflowName
      );

      // !!! Fix hover over context-menu (DELETE LATER) !!!
      await page.locator('.mat-menu-content >> Button >> nth=0').hover();

      await hetidaDesigner.clickOnContextMenu('Delete');
      await hetidaDesigner.clickAnyBtnInDialog('Delete workflow');

      // Check if workflow was deleted
      await hetidaDesigner.typeInSearchTerm(workflowName);

      // Assert
      const searchResult = page.locator('.navigation-container__scrollable');
      await expect(searchResult).toBeEmpty();
    });

    test('Delete component on right-click via context-menu, dialog open', async ({
      page,
      hetidaDesigner
    }) => {
      // Arrange
      const categoryName = 'Draft';
      const componentName = 'Factorial';

      // Act
      await hetidaDesigner.clickWorkflowsComponentsInNavigation('Components');
      await hetidaDesigner.clickCategoryInNavigation(categoryName);
      // Open context-menu via right-click on a component
      await hetidaDesigner.rightClickItemInNavigation(
        categoryName,
        componentName
      );

      // !!! Fix hover over context-menu (DELETE LATER) !!!
      await page.locator('.mat-menu-content >> Button >> nth=0').hover();

      await hetidaDesigner.clickOnContextMenu('Delete');

      // Assert
      const countDialogContainer = await page
        .locator('mat-dialog-container')
        .count();
      expect(countDialogContainer).toEqual(1);
    });

    test('Delete component on right-click via context-menu and confirm dialog', async ({
      page,
      hetidaDesigner
    }) => {
      // Arrange
      const categoryName = 'Draft';
      const componentName = 'Factorial';

      // Act
      await hetidaDesigner.clickWorkflowsComponentsInNavigation('Components');
      await hetidaDesigner.clickCategoryInNavigation(categoryName);
      // Open context-menu via right-click on a component
      await hetidaDesigner.rightClickItemInNavigation(
        categoryName,
        componentName
      );

      // !!! Fix hover over context-menu (DELETE LATER) !!!
      await page.locator('.mat-menu-content >> Button >> nth=0').hover();

      // Delete component on right-click via context-menu
      await hetidaDesigner.clickOnContextMenu('Delete');
      await hetidaDesigner.clickAnyBtnInDialog('Delete component');

      // Check if component was deleted
      await hetidaDesigner.typeInSearchTerm(componentName);

      // Assert
      const searchResult = page.locator('.navigation-container__scrollable');
      await expect(searchResult).toBeEmpty();
    });
  }
);
