import { Page } from '@playwright/test';

export class Navigation {
  private readonly page: Page;

  constructor(page: Page) {
    this.page = page;
  }

  // Tab bar
  public async clickTabNavigation(tabPosition: number): Promise<void> {
    if (tabPosition < 0) {
      console.error(
        `ERROR: Negative tab position, used tab position: ${tabPosition}`
      );
    }

    await this.page.locator(`div[role="tab"] >> nth=${tabPosition}`).click();
  }

  // Left navigation panel
  public async clickBtnNavigation(btnText: string): Promise<void> {
    if (btnText === '') {
      console.error(
        `ERROR: Cannot locate empty text in button, used button: ${btnText}`
      );
    }

    if (btnText === 'Add component' || btnText === 'Add workflow') {
      await this.page.locator(`.add-button:has-text("${btnText}")`).click();
      await this.page.waitForSelector('mat-dialog-container'); // Wait for dialog-container
    } else {
      await this.page.locator(`button:has-text("${btnText}")`).click();
      await this.page.waitForSelector('hd-navigation-category'); // Wait for workflows or components
    }
  }

  public async clickExpansionPanelNavigation(
    categoryName: string
  ): Promise<void> {
    if (categoryName === '') {
      console.error(
        `ERROR: Cannot locate empty category name in "expansion panel", used category: ${categoryName}`
      );
    }

    await this.page.click(
      `mat-expansion-panel-header[role="button"]:has-text("${categoryName}")`
    );
  }

  public async hoverItemNavigation(
    categoryName: string,
    itemName: string
  ): Promise<void> {
    if (categoryName === '' || itemName === '') {
      console.error(
        `ERROR: Cannot locate item in category if one or both names are empty, used item: ${itemName} in category: ${categoryName}`
      );
    }

    await this.page
      .locator(`mat-expansion-panel:has-text("${categoryName}") >> nth=0`)
      .locator(`.navigation-item:has-text("${itemName}") >> nth=0`)
      .hover();
  }

  public async doubleClickItemNavigation(
    categoryName: string,
    itemName: string
  ): Promise<void> {
    if (categoryName === '' || itemName === '') {
      console.error(
        `ERROR: Cannot locate item in category if one or both names are empty, used item: ${itemName} in category: ${categoryName}`
      );
    }

    await this.page
      .locator(`mat-expansion-panel:has-text("${categoryName}") >> nth=0`)
      .locator(`.navigation-item:has-text("${itemName}") >> nth=0`)
      .dblclick();
  }

  public async typeInSearchTerm(searchTerm: string): Promise<void> {
    if (searchTerm === '') {
      console.error(
        `ERROR: Cannot type in empty search term, used search term: ${searchTerm}`
      );
    }

    await this.page
      .locator('.navigation-container__search >> input')
      .type(searchTerm);
  }

  // Open workflows or components, toolbar
  public async clickIconToolbar(iconTitle: string): Promise<void> {
    if (iconTitle === '') {
      console.error(
        `ERROR: Cannot locate empty icon title, used icon title: ${iconTitle}`
      );
    }

    await this.page
      .locator('hd-toolbar')
      .locator(`mat-icon[title="${iconTitle}"]`)
      .click();

    await this.page.waitForSelector('mat-dialog-container'); // Wait for dialog-container
  }

  // Workflows or components-modal-dialog for add, edit, execute etc. functions
  public async clickBtnDialog(btnText: string): Promise<void> {
    if (btnText === '') {
      console.error(
        `ERROR: Cannot locate empty text in button, used button: ${btnText}`
      );
    }

    await this.page.locator(`button:has-text("${btnText}")`).click();
  }

  public async typeInInputDialog(
    inputId: string,
    inputText: string
  ): Promise<void> {
    if (inputId === '' && inputText === '') {
      console.error(
        `ERROR: Cannot locate input field or type in text if input id or input text is empty, used input text: ${inputText} with input id: ${inputId}`
      );
    }

    // Select default input text to overwrite it
    await this.page.locator(`#${inputId}`).click();
    await this.page.press(`#${inputId}`, 'Control+a');
    await this.page.locator(`#${inputId}`).type(inputText);

    if (inputId === 'category') {
      // Tab out of input field to close suggested options
      await this.page.press(`#${inputId}`, 'Tab');
    }
  }
}
