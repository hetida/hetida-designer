import { Page } from '@playwright/test';

export class Navigation {
  private readonly page: Page;

  constructor(page: Page) {
    this.page = page;
  }

  public async clickTabNavigation(tabPosition: number): Promise<void> {
    try {
      if (tabPosition >= 0) {
        await this.page
          .locator(`div[role="tab"] >> nth=${tabPosition}`)
          .click();
      } else {
        throw new Error('ERROR: Negative tab position');
      }
    } catch (error) {
      console.error(`${error}, used tab position: ${tabPosition}`);
    }
  }

  public async clickBtnNavigation(btnText: string): Promise<void> {
    try {
      if (btnText !== '') {
        await this.page.locator(`button:has-text("${btnText}")`).click();
        await this.page.waitForSelector('hd-navigation-category'); // Wait for workflows or components
      } else {
        throw new Error('ERROR: Cannot locate button');
      }
    } catch (error) {
      console.error(`${error}, used button text: ${btnText}`);
    }
  }

  public async clickExpansionPanelNavigation(
    categoryName: string
  ): Promise<void> {
    try {
      if (categoryName !== '') {
        await this.page.click(
          `mat-expansion-panel-header[role="button"]:has-text("${categoryName}")`
        );
      } else {
        throw new Error('ERROR: Cannot locate category "expansion panel"');
      }
    } catch (error) {
      console.error(
        `${error}, used category "expansion panel": ${categoryName}`
      );
    }
  }

  public async hoverItemNavigation(
    categoryName: string,
    itemName: string
  ): Promise<void> {
    try {
      if (categoryName !== '' || itemName !== '') {
        await this.page
          .locator(`mat-expansion-panel:has-text("${categoryName}") >> nth=0`)
          .locator(`.navigation-item:has-text("${itemName}") >> nth=0`)
          .hover();
      } else {
        throw new Error('ERROR: Cannot locate item in category');
      }
    } catch (error) {
      console.error(
        `${error}, used item: ${itemName} in category: ${categoryName}`
      );
    }
  }

  public async doubleClickItemNavigation(
    categoryName: string,
    itemName: string
  ): Promise<void> {
    try {
      if (categoryName !== '' || itemName !== '') {
        await this.page
          .locator(`mat-expansion-panel:has-text("${categoryName}") >> nth=0`)
          .locator(`.navigation-item:has-text("${itemName}") >> nth=0`)
          .dblclick();
      } else {
        throw new Error('ERROR: Cannot locate item in category');
      }
    } catch (error) {
      console.error(
        `${error}, used item: ${itemName} in category: ${categoryName}`
      );
    }
  }

  public async clickIconToolbar(iconTitle: string): Promise<void> {
    try {
      if (iconTitle !== '') {
        await this.page
          .locator('hd-toolbar')
          .locator(`mat-icon[title="${iconTitle}"]`)
          .click();
      } else {
        throw new Error('ERROR: Cannot locate icon');
      }
    } catch (error) {
      console.error(`${error}, used icon: ${iconTitle}`);
    }
  }

  public async clickBtnDialog(btnText: string): Promise<void> {
    try {
      if (btnText !== '') {
        await this.page.locator(`button:has-text("${btnText}")`).click();
      } else {
        throw new Error('ERROR: Cannot locate button');
      }
    } catch (error) {
      console.error(`${error}, used button text: ${btnText}`);
    }
  }

  public async clickInputSearch(): Promise<void> {
    await this.page.locator('.navigation-container__search >> input').click();
  }

  public async typeInSearchTerm(searchTerm: string): Promise<void> {
    try {
      if (searchTerm !== '') {
        await this.page
          .locator('.navigation-container__search >> input')
          .type(searchTerm);
      } else {
        throw new Error('ERROR: Cannot type in search term');
      }
    } catch (error) {
      console.error(`${error}, used search term: ${searchTerm}`);
    }
  }
}
