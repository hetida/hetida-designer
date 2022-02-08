import { Page, BrowserContext } from '@playwright/test';

export class HetidaDesignerDevPage {
    private page: Page;
    private browserContext: BrowserContext;
    private url: string = 'https://hetida-designer.dev.dsa-id.de/';

    constructor(page: Page) {
        this.page = page;
        this.browserContext = page.context();
    }

    // Runs before every test
    public async setupTest(): Promise<void> {
        await this.page.goto(this.url);
    }

    // Runs after every test
    public async clearTest(): Promise<void> {
        await this.browserContext.clearCookies();
    }
}
