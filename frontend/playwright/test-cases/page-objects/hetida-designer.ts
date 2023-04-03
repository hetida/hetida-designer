import { BrowserContext, Page } from '@playwright/test';
import { Moment } from 'moment';

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
    const target = this.page.locator(`${targetHtmlTag}`);

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

    await this.page.waitForSelector(
      `hd-toolbar >> mat-icon[title="${iconTitle}"]:not(.disabled)`
    );

    await this.page
      .locator(`hd-toolbar >> mat-icon[title="${iconTitle}"]`)
      .click();
  }

  public async clickByTestId(testid: string): Promise<void> {
    if (testid === '') {
      throw new Error(`ERROR: Testid must not be empty`);
    }

    await this.page.getByTestId(testid).click();
  }

  public async typeInInput(testid: string, inputText: string): Promise<void> {
    if (testid === '' || inputText === '') {
      throw new Error('ERROR: Testid or input text must not be empty');
    }

    // Select default input text and overwrite it
    await this.page.getByTestId(testid).click();
    await this.page.getByTestId(testid).press('Control+a');
    await this.page.getByTestId(testid).type(inputText);

    // Workaround for autocomplete in create component / workflow dialog
    if (testid === 'category-copy-transformation-dialog') {
      // tab out of input field to close suggested options
      await this.page.getByTestId(testid).press('Tab');
    }
  }
  // TODO
  public async typeInTextarea(textareaText: string): Promise<void> {
    if (textareaText === '') {
      throw new Error('ERROR: Textarea text must not be empty');
    }

    await this.page
      .locator('hd-documentation-editor-dialog >> textarea')
      .click();
    await this.page.press(
      'hd-documentation-editor-dialog >> textarea',
      'Control+a'
    );
    await this.page.press(
      'hd-documentation-editor-dialog >> textarea',
      'Delete'
    );
    await this.page
      .locator('hd-documentation-editor-dialog >> textarea')
      .type(textareaText);
  }
  // TODO
  public async importJson(importData: string): Promise<void> {
    if (importData === '') {
      throw new Error('ERROR: Import data must not be empty');
    }

    await this.page.locator('.editor-container').click();
    await this.page.press('.editor-container >> textarea', 'Control+a');
    await this.page.press('.editor-container >> textarea', 'Delete');
    await this.page.locator('.editor-container >> textarea').type(importData);
  }

  public async selectItemInDropdown(
    dropdownId: string,
    itemText: string
  ): Promise<void> {
    if (dropdownId === '' || itemText === '') {
      throw new Error(`ERROR: Dropdown id or item text must not be empty`);
    }

    await this.page.getByTestId(dropdownId).click();
    await this.page.locator(`mat-option:has-text("${itemText}")`).click();
  }

  public async selectSourceSearchResult(
    SearchResultPosition: number
  ): Promise<void> {
    if (SearchResultPosition < 0) {
      throw new Error(
        `ERROR: Negative search result position, used search result position: ${SearchResultPosition}`
      );
    }

    await this.page
      .locator(
        `hd-node-search >> cdk-virtual-scroll-viewport >> div >> .node-item >> nth=${SearchResultPosition}`
      )
      .click();
  }

  public async selectTimestampRange(from: Moment, to: Moment): Promise<void> {
    if (from === undefined || to === undefined) {
      throw new Error(`ERROR: From or to date must not be empty`);
    }

    const timestampRange: Moment[] = [from, to];

    for (const timestamp of timestampRange) {
      await this.page.locator('.owl-dt-container-from[role="radio"]').click();
      await this.page
        .locator('button[aria-label="Choose month and year"]')
        .click();
      await this.page.locator(`td[aria-label="${timestamp.year()}"]`).click();
      await this.page
        .locator(`td[aria-label="${timestamp.format('MMMM YYYY')}"]`)
        .click();
      await this.page
        .locator(`td[aria-label="${timestamp.format('MMMM D, YYYY')}"]`)
        .click();
      await this.page
        .locator('input[class="owl-dt-timer-input"] >> nth=0')
        .click();
      await this.page.press(
        'input[class="owl-dt-timer-input"] >> nth=0',
        'Control+a'
      );
      await this.page
        .locator('input[class="owl-dt-timer-input"] >> nth=0')
        .type(timestamp.hours().toString());
      await this.page
        .locator('input[class="owl-dt-timer-input"] >> nth=1')
        .click();
      await this.page.press(
        'input[class="owl-dt-timer-input"] >> nth=1',
        'Control+a'
      );
      await this.page
        .locator('input[class="owl-dt-timer-input"] >> nth=1')
        .type(timestamp.minutes().toString());
    }

    await this.page
      .locator('owl-date-time-container >> button:has-text("Set")')
      .click();
  }
}
