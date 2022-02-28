import { Page, BrowserContext } from '@playwright/test';
const URL = require('./../../url.config.json');

export class HetidaDesigner {
  private readonly page: Page;
  private readonly browserContext: BrowserContext;
  private readonly url: string;

  constructor(page: Page) {
    this.page = page;
    this.browserContext = page.context();
    this.url = URL.url;

    if (this.url === '' || this.url === undefined) {
      console.error(
        'Please change the URL in "url.config.json" with your Hetida Designer URL, you wish to run e2e-tests on!'
      );
    }
  }

  // Run before every test
  public async setupTest(): Promise<void> {
    await this.page.goto(this.url);
  }

  // Run after every test
  public async clearTest(): Promise<void> {
    await this.browserContext.clearCookies();
  }
}
