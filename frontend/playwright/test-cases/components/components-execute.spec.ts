import { test } from '@playwright/test';
import { HetidaDesigner } from '../page-objects/hetida-designer';
import { Navigation } from '../page-objects/navigation';
import { ErrorNotification } from '../page-objects/error-notification';
import { Component } from '../page-objects/component';

test('Execute components', async ({ page }) => {
  const hetidaDesigner = new HetidaDesigner(page);
  const navigation = new Navigation(page);
  const errorNotification = new ErrorNotification(page);
  const component = new Component(page, navigation, errorNotification);
  // Test parameter
  const categoryName = 'Arithmetic';
  const componentName = 'Pi';

  // Run setup
  await hetidaDesigner.setupTest();

  // Run test
  await component.executeComponent(categoryName, componentName);

  // Run clear
  await hetidaDesigner.clearTest();
});
