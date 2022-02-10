import { Page } from '@playwright/test';

export class Navigation {
  private page: Page;

  constructor(page: Page) {
    this.page = page;
  }

  public async clickTabNavigation(tabPosition: number): Promise<void> {
    if (tabPosition >= 0) {
      await this.page.locator('div[role="tab"] >> nth=' + tabPosition + '').click();
    } else {
      console.error('ERROR: Negative tab position! ' + tabPosition);
    }
  }

  public async clickBtnNavigation(btnText: String): Promise<void> {
    if (btnText !== '') {
      await this.page.locator('button:has-text("' + btnText + '")').click();
      await this.page.waitForSelector('hd-navigation-category'); // Wait for workflows or components
    } else {
      console.error('ERROR: Cannot locate button! ' + btnText);
    }
  }

  public async clickExpansionPanelNavigation(panelTitle: String): Promise<void> {
    if (panelTitle !== '') {
      await this.page.click('mat-expansion-panel-header[role="button"]:has-text("' + panelTitle + '")');
    } else {
      console.error('ERROR: Cannot locate expansion panel! ' + panelTitle);
    }
  }
}
