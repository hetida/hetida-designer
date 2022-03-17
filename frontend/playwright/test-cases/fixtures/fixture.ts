import { Page, test as base } from '@playwright/test';
import { HetidaDesigner } from '../page-objects/hetida-designer';

type HetidaDesignerFixture = {
  page: Page;
  hetidaDesigner: HetidaDesigner;
};

export const test = base.extend<HetidaDesignerFixture>({
  page: async ({ baseURL, page }, use) => {
    page.on('console', msg => {
      if (msg.type() === 'error') {
        // this makes tests fail whenever an error is logged to the browser console
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
