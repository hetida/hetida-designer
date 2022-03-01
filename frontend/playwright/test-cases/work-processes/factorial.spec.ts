import { test, expect } from '@playwright/test';
import { HetidaDesigner } from '../page-objects/hetida-designer';
import { Navigation } from '../page-objects/navigation';

test('Create a "factorial" component and use it, in a new created workflow', async ({
  page
}) => {
  const hetidaDesigner = new HetidaDesigner(page);
  const navigation = new Navigation(page);
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
