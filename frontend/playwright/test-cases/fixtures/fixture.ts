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
        const messages = msg.text().split('\n');

        for (const message of messages) {
          // this makes tests fail whenever an error is logged to the browser console
          throw new Error(message);
        }
      }
    });

    await page.goto(baseURL, {
      waitUntil: 'domcontentloaded'
    });
    await use(page);
  },

  hetidaDesigner: async ({ page }, use) => {
    const hetidaDesigner = new HetidaDesigner(page);
    await use(hetidaDesigner);
  }
});

export { expect } from '@playwright/test';
