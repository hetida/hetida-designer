import { Page } from '@playwright/test';

export class Navigation {
  private readonly page: Page;

  constructor(page: Page) {
    this.page = page;
  }

  public async clickTabNavigation(tabPosition: number): Promise<void> {
    if (tabPosition >= 0) {
      await this.page.locator(`div[role="tab"] >> nth=${tabPosition}`).click();
    } else {
      console.error(`ERROR: Negative tab position! ${tabPosition}`);
    }
  }

  public async clickBtnNavigation(btnText: string): Promise<void> {
    if (btnText !== '') {
      await this.page.locator(`button:has-text("${btnText}")`).click();
      await this.page.waitForSelector('hd-navigation-category'); // Wait for workflows or components
    } else {
      console.error(`ERROR: Cannot locate button! ${btnText}`);
    }
  }

  public async clickExpansionPanelNavigation(
    categoryName: string
  ): Promise<void> {
    if (categoryName !== '') {
      await this.page.click(
        `mat-expansion-panel-header[role="button"]:has-text("${categoryName}")`
      );
    } else {
      console.error(
        `ERROR: Cannot locate category "expansion panel"! ${categoryName}`
      );
    }
  }

  public async hoverItemNavigation(
    categoryName: string,
    itemName: string
  ): Promise<void> {
    if (categoryName !== '' || itemName !== '') {
      await this.page
        .locator(`mat-expansion-panel:has-text("${categoryName}") >> nth=0`)
        .locator(`.navigation-item:has-text("${itemName}") >> nth=0`)
        .hover();
    } else {
      console.error(
        `ERROR: Cannot locate item ${itemName} in category ${categoryName}!`
      );
    }
  }

  public async doubleClickItemNavigation(
    categoryName: string,
    itemName: string
  ): Promise<void> {
    if (categoryName !== '' || itemName !== '') {
      await this.page
        .locator(`mat-expansion-panel:has-text("${categoryName}") >> nth=0`)
        .locator(`.navigation-item:has-text("${itemName}") >> nth=0`)
        .dblclick();
    } else {
      console.error(
        `ERROR: Cannot locate item ${itemName} in category ${categoryName}!`
      );
    }
  }

  public async clickIconToolbar(iconTitle: string): Promise<void> {
    if (iconTitle !== '') {
      await this.page
        .locator('hd-toolbar')
        .locator(`mat-icon[title="${iconTitle}"]`)
        .click();
    } else {
      console.error(`ERROR: Cannot locate icon! ${iconTitle}`);
    }
  }

  public async clickBtnDialog(btnText: string): Promise<void> {
    if (btnText !== '') {
      await this.page.locator(`button:has-text("${btnText}")`).click();
    } else {
      console.error(`ERROR: Cannot locate button! ${btnText}`);
    }
  }
}
