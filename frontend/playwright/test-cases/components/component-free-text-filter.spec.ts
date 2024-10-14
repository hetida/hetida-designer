import { expect, test } from '../fixtures/fixture';

test('Free text filter for component', async ({
  page,
  hetidaDesigner,
  browserName
}) => {
  // Arrange
  const componentCategory = 'Test';
  const componentName = `Test free text filter for component ${browserName}`;
  const componentDescription = 'Free text filter for component';
  const componentTag = '0.1.0';
  const componentInputName = 'input';
  const componentOutputName = 'output';
  const adapter = 'Python-Demo-Adapter';
  const source = 'Temperature Unit';
  const dataType = 'STRING';

  // Act
  // Add a new test component
  await hetidaDesigner.clickComponentsInNavigation();
  await hetidaDesigner.clickAddButtonInNavigation('Add component');
  await page.waitForSelector(
    'mat-dialog-container:has-text("Create new component")'
  );
  await hetidaDesigner.typeInInputById('name', componentName);
  await hetidaDesigner.typeInInputById('category', componentCategory);
  await hetidaDesigner.typeInInputById('description', componentDescription);
  await hetidaDesigner.typeInInputById('tag', componentTag);
  await hetidaDesigner.clickByTestId(
    'create component-copy-transformation-dialog'
  );

  // Configure component I/O
  await hetidaDesigner.clickIconInToolbar('Configure I/O');
  await page.waitForSelector(
    `mat-dialog-container:has-text("Configure Input / Output for Component ${componentName} ${componentTag}")`
  );
  await hetidaDesigner.clickByTestId('add-input-component-io-dialog');
  await hetidaDesigner.typeInInputByTestId(
    'new_input_1-label-input-component-io-dialog',
    componentInputName
  );

  // Select Data Type
  await hetidaDesigner.selectItemInDropdown(
    `${componentInputName}-data-type-input-component-io-dialog`,
    dataType
  );

  await hetidaDesigner.clickByTestId('add-output-component-io-dialog');
  await hetidaDesigner.typeInInputByTestId(
    'new_output_1-label-output-component-io-dialog',
    componentOutputName
  );

  await hetidaDesigner.clickByTestId('save-component-io-dialog');

  // Execute component and get the protocol
  await hetidaDesigner.clickIconInToolbar('Execute');
  await page.waitForSelector(
    `mat-dialog-container:has-text("Execute Component ${componentName} ${componentTag}")`
  );

  // Select adapter
  await hetidaDesigner.selectItemInDropdown(
    `${componentInputName}-adapter-list-input-wiring-dialog`,
    adapter
  );

  // Select source
  await hetidaDesigner.clickByTestId(
    `${componentInputName}-browse-sources-input-wiring-dialog`
  );
  await page.waitForSelector('mat-dialog-container:has-text("Search Sources")');
  await hetidaDesigner.typeInInputByTestId('search-tree-node', source);
  await hetidaDesigner.selectSourceSearchResult(0);
  await hetidaDesigner.clickByTestId(
    `${componentInputName}-node-wiring-context-menu`
  );
  await page.mouse.click(0, 0); // Close context menu
  await hetidaDesigner.clickByTestId('done-tree-node-modal'); // Close Source Dialog
  await hetidaDesigner.clickByTestId('cancel-wiring-dialog'); // Close Execute Dialog

  const freeTextInput = page.getByTestId(
    `${componentInputName}-free-text-filter-input-wiring-dialog`
  );

  expect(freeTextInput).toBeTruthy();
});

test.afterEach(async ({ page, hetidaDesigner, browserName }) => {
  // Clear
  const componentCategory = 'Test';
  const componentName = `Test free text filter for component ${browserName}`;
  const componentTag = '0.1.0';

  await hetidaDesigner.clickComponentsInNavigation();
  await hetidaDesigner.clickCategoryInNavigation(componentCategory);
  await hetidaDesigner.rightClickItemInNavigation(
    componentCategory,
    componentName
  );
  await page.locator('.mat-mdc-menu-panel').hover();
  await hetidaDesigner.clickOnContextMenu('Delete');
  await page.waitForSelector(
    `mat-dialog-container:has-text("Delete component ${componentName} (${componentTag})")`
  );
  await hetidaDesigner.clickByTestId('delete component-confirm-dialog');

  await hetidaDesigner.clearTest();
});
