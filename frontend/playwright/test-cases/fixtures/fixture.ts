import { test as base, Page } from '@playwright/test';
import { HetidaDesigner } from '../page-objects/hetida-designer';
import { Navigation } from '../page-objects/navigation';
import { ErrorNotification } from '../page-objects/error-notification';

type HetidaDesignerFixture = {
  page: Page;
  hetidaDesigner: HetidaDesigner;
  navigation: Navigation;
  errorNotification: ErrorNotification;
};

export const test = base.extend<HetidaDesignerFixture>({
  page: async ({ baseURL, page }, use) => {
    await page.goto(baseURL);
    await use(page);
  },

  hetidaDesigner: async ({ page }, use) => {
    const hetidaDesigner = new HetidaDesigner(page);
    await use(hetidaDesigner);
  },

  navigation: async ({ page }, use) => {
    const navigation = new Navigation(page);
    await use(navigation);
  },

  errorNotification: async ({ page }, use) => {
    const errorNotification = new ErrorNotification(page);
    await use(errorNotification);
  }
});

export { expect } from '@playwright/test';
