import { Page, BrowserContext } from '@playwright/test';

export class HetidaDesigner {
  private readonly page: Page;
  private readonly browserContext: BrowserContext;

  constructor(page: Page) {
    this.page = page;
    this.browserContext = page.context();
  }

  // Run after every test
  public async clearTest(): Promise<void> {
    await this.browserContext.clearCookies();
    await this.page.reload();
  }

  // Navigation
  // Tab bar
  public async clickTabInNavigation(tabPosition: number): Promise<void> {
    if (tabPosition < 0) {
      throw new Error(
        `ERROR: Negative tab position, used tab position: ${tabPosition}`
      );
    }

    await this.page.locator(`div[role="tab"] >> nth=${tabPosition}`).click();
  }

  // Left navigation
  public async clickWorkflowsComponentsInNavigation(
    btnText: string
  ): Promise<void> {
    if (btnText === '') {
      throw new Error(
        `ERROR: Cannot locate empty text in button, used button: ${btnText}`
      );
    }

    await this.page.locator(`button:has-text("${btnText}")`).click();
    await this.page.waitForSelector('hd-navigation-category');
  }

  public async clickAddWorkflowComponentInNavigation(
    btnText: string
  ): Promise<void> {
    if (btnText === '') {
      throw new Error(
        `ERROR: Cannot locate empty text in button, used button: ${btnText}`
      );
    }

    await this.page.locator(`.add-button:has-text("${btnText}")`).click();
    await this.page.waitForSelector('mat-dialog-container');
  }

  public async clickCategoryInNavigation(categoryName: string): Promise<void> {
    if (categoryName === '') {
      throw new Error(
        `ERROR: Cannot locate empty category name in "expansion panel", used category: ${categoryName}`
      );
    }

    await this.page.click(
      `mat-expansion-panel-header[role="button"]:has-text("${categoryName}")`
    );
  }

  public async hoverItemInNavigation(
    categoryName: string,
    itemName: string
  ): Promise<void> {
    if (categoryName === '' || itemName === '') {
      throw new Error(
        `ERROR: Cannot locate item in category, if one or both names are empty, used item: ${itemName} in category: ${categoryName}`
      );
    }

    await this.page
      .locator(`mat-expansion-panel:has-text("${categoryName}") >> nth=0`)
      .locator(`.navigation-item:has-text("${itemName}") >> nth=0`)
      .hover();
  }

  public async doubleClickItemInNavigation(
    categoryName: string,
    itemName: string
  ): Promise<void> {
    if (categoryName === '' || itemName === '') {
      throw new Error(
        `ERROR: Cannot locate item in category, if one or both names are empty, used item: ${itemName} in category: ${categoryName}`
      );
    }

    await this.page
      .locator(`mat-expansion-panel:has-text("${categoryName}") >> nth=0`)
      .locator(`.navigation-item:has-text("${itemName}") >> nth=0`)
      .dblclick();
  }

  public async rightClickItemInNavigation(
    categoryName: string,
    itemName: string
  ): Promise<void> {
    if (categoryName === '' || itemName === '') {
      throw new Error(
        `ERROR: Cannot locate item in category, if one or both names are empty, used item: ${itemName} in category: ${categoryName}`
      );
    }

    await this.page
      .locator(`mat-expansion-panel:has-text("${categoryName}") >> nth=0`)
      .locator(`.navigation-item:has-text("${itemName}") >> nth=0`)
      .click({ button: 'right' });
  }

  public async clickOnContextMenu(itemMenu: string): Promise<void> {
    if (itemMenu === '') {
      throw new Error(
        `ERROR: Cannot locate empty item in context-menu, used item: ${itemMenu}`
      );
    }

    await this.page
      .locator(`.mat-menu-content >> button:has-text("${itemMenu}")`)
      .click();
  }

  public async typeInSearchTerm(searchTerm: string): Promise<void> {
    if (searchTerm === '') {
      throw new Error(
        `ERROR: Cannot type in empty search term, used search term: ${searchTerm}`
      );
    }

    await this.page
      .locator('.navigation-container__search >> input')
      .type(searchTerm);
  }

  // Open workflows or components, toolbar
  public async clickIconInToolbar(iconTitle: string): Promise<void> {
    if (iconTitle === '') {
      throw new Error(
        `ERROR: Cannot locate empty icon title, used icon title: ${iconTitle}`
      );
    }

    await this.page
      .locator('hd-toolbar')
      .locator(`mat-icon[title="${iconTitle}"]`)
      .click();
  }

  // Workflows or components-modal-dialog for add, edit, execute etc. functions
  public async clickAnyBtnInDialog(btnText: string): Promise<void> {
    if (btnText === '') {
      throw new Error(
        `ERROR: Cannot locate empty text in button, used button: ${btnText}`
      );
    }

    await this.page.locator(`button:has-text("${btnText}")`).click();
  }

  public async typeInAnyInputInDialog(
    inputId: string,
    inputText: string
  ): Promise<void> {
    if (inputId === '' || inputText === '') {
      throw new Error(
        `ERROR: Cannot locate input field or type in text, if input id or input text is empty, used input text: ${inputText} with input id: ${inputId}`
      );
    }

    // Select default input text and overwrite it
    await this.page.locator(`#${inputId}`).click();
    await this.page.press(`#${inputId}`, 'Control+a');
    await this.page.locator(`#${inputId}`).type(inputText);

    if (inputId === 'category') {
      // Tab out of input field to close suggested options
      await this.page.press(`#${inputId}`, 'Tab');
    }
  }
}
