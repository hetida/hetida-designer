import { expect, Page } from '@playwright/test';

export class HetidaDesignerDevPage {
    private page: Page;
    private url: string = 'https://hetida-designer.dev.dsa-id.de/';

    constructor(page: Page) {
        this.page = page;
    }

    public async setup(): Promise<void> {
        await this.page.goto(this.url);
        await expect(this.page).toHaveTitle('hetida designer');

        await this.page.locator('div[role="tab"] div:has-text("home")').click();
        await expect(this.page.locator('.home-header h1')).toHaveText('Welcome to hetida designer');
    }
}
