import { test as base, Page } from '@playwright/test';
import { HetidaDesigner } from '../page-objects/hetida-designer';

type HetidaDesignerFixture = {
  page: Page;
  hetidaDesigner: HetidaDesigner;
};

export const test = base.extend<HetidaDesignerFixture>({
  // Throw a new error, on console error in browser
  page: async ({ baseURL, page }, use) => {
    page.on('console', msg => {
      if (msg.type() === 'error') {
        throw new Error(msg.text());
      }
    });

    await page.goto(baseURL);
    await use(page);
  },

  hetidaDesigner: async ({ page }, use) => {
    const hetidaDesigner = new HetidaDesigner(page);
    await use(hetidaDesigner);
  }
});

export { expect } from '@playwright/test';
