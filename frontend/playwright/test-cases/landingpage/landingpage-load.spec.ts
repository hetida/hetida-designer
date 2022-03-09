import { test, expect } from '../fixtures/fixture';

test('Load landingpage', async ({ page, hetidaDesigner }) => {
  // Run test
  await expect(page).toHaveTitle('hetida designer');

  const homeHeader = page.locator('.home-header h1');
  await expect(homeHeader).toHaveText('Welcome to hetida designer');

  // Run clear
  await hetidaDesigner.clearTest();
});
