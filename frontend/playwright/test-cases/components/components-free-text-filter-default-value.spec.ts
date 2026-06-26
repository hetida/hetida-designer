import { expect, test } from '../fixtures/fixture';

test('Send a default_value via adapter for the free_text filter to initialise, if not null', async ({
  page,
  hetidaDesigner
}) => {
  // Arrange
  const componentCategory = 'Visualization';
  const componentName = 'Single Timeseries Plot';
  const componentTag = '1.0.0';
  const componentInputName = 'series';
  const adapter = 'Python-Demo-Adapter';
  const source = 'Influx Temperature';
  const defaultValue = '1h';

  // Act
  await hetidaDesigner.clickComponentsInNavigation();
  await hetidaDesigner.clickCategoryInNavigation(componentCategory);
  await hetidaDesigner.doubleClickItemInNavigation(
    `${componentName}(${componentTag})`
  );

  // Configure Execute
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

  const inputFreeText = await page
    .getByTestId(`${componentInputName}-free-text-filter-input-wiring-dialog`)
    .inputValue();

  // Assert
  expect(inputFreeText).toEqual(defaultValue);
});

test.afterEach(async ({ hetidaDesigner }) => {
  // Clear
  await hetidaDesigner.clearTest();
});
