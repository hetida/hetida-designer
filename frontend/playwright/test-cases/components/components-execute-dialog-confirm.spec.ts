import { expect, test } from '../fixtures/fixture';

test('Confirm "execute component" dialog', async ({ page, hetidaDesigner }) => {
  // Arrange
  const categoryName = 'Arithmetic';
  const componentName = 'Pi';

  // Act
  await hetidaDesigner.clickComponentsInNavigation();
  await hetidaDesigner.clickCategoryInNavigation(categoryName);
  await hetidaDesigner.doubleClickItemInNavigation(categoryName, componentName);

  await hetidaDesigner.clickIconInToolbar('Execute');
  await page.waitForSelector('mat-dialog-container');

  await hetidaDesigner.clickByTestId('execute-wiring-dialog');
  await page.waitForSelector('hd-protocol-viewer');

  // Assert
  const protocolViewer = page.locator('hd-protocol-viewer');
  await expect(protocolViewer).toBeVisible();
  await expect(protocolViewer).not.toBeEmpty();

  await hetidaDesigner.clearTest();
});
