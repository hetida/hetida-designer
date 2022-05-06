import { BrowserContext, Page } from '@playwright/test';

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
  }

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
    buttonText: string
  ): Promise<void> {
    if (buttonText === '') {
      throw new Error('ERROR: Button text must not be empty');
    }

    await this.page.locator(`button:has-text("${buttonText}")`).click();
    await this.page.waitForSelector('hd-navigation-category');
  }

  public async clickAddWorkflowComponentInNavigation(
    buttonText: string
  ): Promise<void> {
    if (buttonText === '') {
      throw new Error('ERROR: Button text must not be empty');
    }

    await this.page.locator(`.add-button:has-text("${buttonText}")`).click();
    await this.page.waitForSelector('mat-dialog-container');
  }

  public async clickCategoryInNavigation(categoryName: string): Promise<void> {
    if (categoryName === '') {
      throw new Error('ERROR: Category name must not be empty');
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
      throw new Error('ERROR: Category name and item name must not be empty');
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
      throw new Error('ERROR: Category name and item name must not be empty');
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
      throw new Error('ERROR: Category name and item name must not be empty');
    }

    await this.page
      .locator(`mat-expansion-panel:has-text("${categoryName}") >> nth=0`)
      .locator(`.navigation-item:has-text("${itemName}") >> nth=0`)
      .click({ button: 'right' });
  }

  public async dragAndDropItemInNavigation(
    categoryName: string,
    itemName: string,
    targetHtmlTag: string
  ): Promise<void> {
    if (categoryName === '' || itemName === '' || targetHtmlTag === '') {
      throw new Error(
        'ERROR: Category name, target html tag and item name must not be empty'
      );
    }

    const source = this.page
      .locator(`mat-expansion-panel:has-text("${categoryName}") >> nth=0`)
      .locator(`.navigation-item:has-text("${itemName}") >> nth=0`);
    const target = this.page.locator(
      'svg:has-text(".svg-small-grid { stroke: #a9a9a9; } .svg-grid { stroke: #a9a9a9; }") >> nth=0'
    );

    await source.dragTo(target);
  }

  public async clickOnContextMenu(menuItem: string): Promise<void> {
    if (menuItem === '') {
      throw new Error('ERROR: Menu item must not be empty');
    }

    await this.page
      .locator(`.mat-menu-content >> button:has-text("${menuItem}")`)
      .click();
  }

  public async typeInSearchTerm(searchTerm: string): Promise<void> {
    if (searchTerm === '') {
      throw new Error('ERROR: Search term must not be empty');
    }

    await this.page
      .locator('.navigation-container__search >> input')
      .type(searchTerm);
  }

  public async clickIconInToolbar(iconTitle: string): Promise<void> {
    if (iconTitle === '') {
      throw new Error('ERROR: Icon title must not be empty');
    }

    await this.page
      .locator('hd-toolbar')
      .locator(`mat-icon[title="${iconTitle}"]`)
      .click();
  }

  public async clickButton(buttonText: string): Promise<void> {
    if (buttonText === '') {
      throw new Error('ERROR: Button text must not be empty');
    }

    const locateButtons = this.page.locator(`button:has-text("${buttonText}")`);
    const countButtons = await locateButtons.count();
    // If more than one button with the same text was found, click the enabled one
    if (countButtons > 1) {
      for (let i = 0; i < countButtons; i++) {
        if (await locateButtons.nth(i).isEnabled()) {
          await locateButtons.nth(i).click();
        }
      }
    } else {
      await locateButtons.click();
    }
  }

  public async clickToggleButton(toggleButtonPosition: number): Promise<void> {
    if (toggleButtonPosition < 1) {
      throw new Error('ERROR: Toggle button starts at position 1');
    }

    await this.page
      .locator(`#mat-slide-toggle-${toggleButtonPosition} label`)
      .click();
  }

  public async clickInput(inputPosition: number): Promise<void> {
    if (inputPosition < 0) {
      throw new Error('ERROR: Negative input position');
    }

    await this.page
      .locator(`input[type="text"] >> nth=${inputPosition}`)
      .click();
  }

  public async typeInInput(inputId: string, inputText: string): Promise<void> {
    if (inputId === '' || inputText === '') {
      throw new Error('ERROR: Input id or text must not be empty');
    }

    // Select default input text and overwrite it
    await this.page.locator(`#${inputId}`).click();
    await this.page.press(`#${inputId}`, 'Control+a');
    await this.page.locator(`#${inputId}`).type(inputText);

    // Workaround for autocomplete in create component / workflow dialog
    if (inputId === 'category') {
      // Tab out of input field to close suggested options
      await this.page.press(`#${inputId}`, 'Tab');
    }
  }

  public async typeInInputPosition(
    inputPosition: number,
    inputText: string
  ): Promise<void> {
    if (inputPosition < 0 || inputText === '') {
      throw new Error('ERROR: Input position or text must not be empty');
    }

    await this.page
      .locator(`input[type="text"] >> nth=${inputPosition}`)
      .click();
    await this.page.press(
      `input[type="text"] >> nth=${inputPosition}`,
      'Control+a'
    );
    await this.page
      .locator(`input[type="text"] >> nth=${inputPosition}`)
      .type(inputText);
  }

  public async importJson(importData: string): Promise<void> {
    if (importData === '') {
      throw new Error('ERROR: Import data must not be empty');
    }

    await this.page.locator('.view-line').click();
    await this.page.press('.view-line', 'Control+a');
    await this.page.locator('.view-line').type(importData);
  }
}
