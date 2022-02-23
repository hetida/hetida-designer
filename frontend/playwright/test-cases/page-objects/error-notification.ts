import { Page, expect } from '@playwright/test';

export class ErrorNotification {
  private readonly page: Page;

  constructor(page: Page) {
    this.page = page;
  }

  // Check if error-notification occurred
  public async checkErrorNotification(): Promise<void> {
    let countErrorNotification = 0;

    try {
      // Wait 3 sec. for error-notification
      await this.page.waitForSelector('.error-notification-overlay', {
        timeout: 3000
      });

      countErrorNotification = await this.page
        .locator('.error-notification-overlay')
        .count();
    } catch (error) {}

    expect(countErrorNotification).toEqual(0);
  }
}
