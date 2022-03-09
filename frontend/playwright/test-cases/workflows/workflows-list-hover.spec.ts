import { test, expect } from '../fixtures/fixture';

test('Hover over workflow, check if error-notification occurred', async ({
  hetidaDesigner,
  navigation,
  errorNotification
}) => {
  // Test parameter
  const categoryName = 'Examples';
  const workflowName = 'Volatility Detection Example';

  // Run test
  await navigation.clickBtnNavigation('Workflows');
  await navigation.clickExpansionPanelNavigation(categoryName);
  // Hover over workflow in category
  await navigation.hoverItemNavigation(categoryName, workflowName);

  // Check if error-notification occurred
  const countErrorNotification = await errorNotification.checkErrorNotification();
  expect(countErrorNotification).toEqual(0);

  // Run clear
  await hetidaDesigner.clearTest();
});
