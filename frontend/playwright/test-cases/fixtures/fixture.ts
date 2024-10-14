import { Page, test as base } from '@playwright/test';
import { HetidaDesigner } from '../page-objects/hetida-designer';

type HetidaDesignerFixture = {
  page: Page;
  hetidaDesigner: HetidaDesigner;
};

export const test = base.extend<HetidaDesignerFixture>({
  page: async ({ baseURL, page }, use) => {
    page.on('console', msg => {
      const ignoreErrorMessages = [
        '[ERROR] 0-undefined - The authority URL MUST be provided in the configuration! ',
        '[ERROR] 0-undefined - The clientId is required and missing from your config!',
        '[ERROR] 0-undefined - Validation of config rejected with errors. Config is NOT set.'
      ];

      if (msg.type() === 'error') {
        const messages = msg.text().split('\n');

        for (const message of messages) {
          if (!ignoreErrorMessages.includes(message)) {
            // this makes tests fail whenever an error is logged to the browser console
            throw new Error(message);
          }
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
