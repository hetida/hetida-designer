import { test, expect } from '@playwright/test';
import { HetidaDesigner } from '../page-objects/hetida-designer';
import { Navigation } from '../page-objects/navigation';

test('Execute workflows', async ({ page }) => {
  const hetidaDesigner = new HetidaDesigner(page);
  const navigation = new Navigation(page);

  // Run setup
  await hetidaDesigner.setupTest();

  // Run test


  // Run clear
  await hetidaDesigner.clearTest();
});
