import { test } from '@playwright/test';
import { HetidaDesigner } from '../page-objects/hetida-designer';
import { Navigation } from '../page-objects/navigation';
import { ErrorNotification } from '../page-objects/error-notification';
import { Workflow } from '../page-objects/workflow';

test('Open workflows on double-click', async ({ page }) => {
  const hetidaDesigner = new HetidaDesigner(page);
  const navigation = new Navigation(page);
  const errorNotification = new ErrorNotification(page);
  const workflow = new Workflow(page, navigation, errorNotification);
  // Test parameter
  const categoryName = 'Examples';
  const workflowName = 'Volatility Detection Example';

  // Run setup
  await hetidaDesigner.setupTest();

  // Run test
  workflow.openWorkflow(categoryName, workflowName);

  // Run clear
  await hetidaDesigner.clearTest();
});
