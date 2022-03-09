import { test, expect } from '../fixtures/fixture';

test('Load components list', async ({ page, hetidaDesigner, navigation }) => {
  // Run test
  await navigation.clickBtnNavigation('Components');

  const countComponents = await page.locator('hd-navigation-category').count();
  expect(countComponents).toBeGreaterThan(0);

  // Run clear
  await hetidaDesigner.clearTest();
});
