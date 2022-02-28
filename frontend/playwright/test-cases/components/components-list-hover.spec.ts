import { test, expect } from '@playwright/test';
import { HetidaDesigner } from '../page-objects/hetida-designer';
import { Navigation } from '../page-objects/navigation';
import { ErrorNotification } from '../page-objects/error-notification';

test('Hover over component, check if error-notification occurred', async ({
  page
}) => {
  const hetidaDesigner = new HetidaDesigner(page);
  const navigation = new Navigation(page);
  const errorNotification = new ErrorNotification(page);
  // Test parameter
  const categoryName = 'Arithmetic';
  const componentName = 'Pi';

  // Run setup
  await hetidaDesigner.setupTest();

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
