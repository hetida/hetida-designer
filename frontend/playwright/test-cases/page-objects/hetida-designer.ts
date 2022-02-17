import { Page, BrowserContext } from '@playwright/test';

export class HetidaDesigner {
  private readonly page: Page;
  private readonly browserContext: BrowserContext;
  private readonly url = 'https://hetida-designer.dev.dsa-id.de/'; // Dev system
  // private url: string = 'https://hetida-designer-demo.dev.dsa-id.de/'; // Demo system

  constructor(page: Page) {
    this.page = page;
    this.browserContext = page.context();
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
