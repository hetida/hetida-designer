import { test, expect } from '../fixtures/fixture';

test('Hover over component, check if error-notification occurred', async ({
  hetidaDesigner,
  navigation,
  errorNotification
}) => {
  // Test parameter
  const categoryName = 'Arithmetic';
  const componentName = 'Pi';

  // Run test
  await navigation.clickBtnNavigation('Components');
  await navigation.clickExpansionPanelNavigation(categoryName);
  // Hover over component in category
  await navigation.hoverItemNavigation(categoryName, componentName);

  // Check if error-notification occurred
  const countErrorNotification = await errorNotification.checkErrorNotification();
  expect(countErrorNotification).toEqual(0);

  // Run clear
  await hetidaDesigner.clearTest();
});
