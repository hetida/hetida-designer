import { test, expect } from '../fixtures/fixture';

test('Execute components, confirm dialog', async ({ page, hetidaDesigner }) => {
  // Arrange
  const categoryName = 'Arithmetic';
  const componentName = 'Pi';

  // Act
  await hetidaDesigner.clickWorkflowsComponentsInNavigation('Components');
  await hetidaDesigner.clickCategoryInNavigation(categoryName);
  await hetidaDesigner.doubleClickItemInNavigation(categoryName, componentName);

  await hetidaDesigner.clickIconInToolbar('Execute');
  await page.waitForSelector('mat-dialog-container');

  await hetidaDesigner.clickAnyBtnInDialog('Execute');
  await page.waitForSelector('hd-protocol-viewer');

  // Assert
  const visibleProtocolViewer = page.locator('hd-protocol-viewer');
  await expect(visibleProtocolViewer).toBeVisible();
  await expect(visibleProtocolViewer).not.toBeEmpty();

  // Run clear
  await hetidaDesigner.clearTest();
});
