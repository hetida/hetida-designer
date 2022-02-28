import { test, expect } from '@playwright/test';
import { HetidaDesigner } from '../page-objects/hetida-designer';
import { Navigation } from '../page-objects/navigation';
import { ErrorNotification } from '../page-objects/error-notification';
import { Component } from '../page-objects/component';
import { Workflow } from '../page-objects/workflow';

test('Create a "factorial" component and use it, in a new created workflow', async ({
  page
}) => {
  const hetidaDesigner = new HetidaDesigner(page);
  const navigation = new Navigation(page);
  const errorNotification = new ErrorNotification(page);
  const component = new Component(page, navigation, errorNotification);
  const workflow = new Workflow(page, navigation, errorNotification);
  // Test parameter
  const categoryName = 'Draft';
  const componentName = 'Factorial';
  const shortDescription = 'Calculates my factorial';
  const tag = '1.0.0';

  // Run setup
  await hetidaDesigner.setupTest();

  // Run test

  // Run clear
  await hetidaDesigner.clearTest();
});
