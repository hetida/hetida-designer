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

  // TODO use test ids
  public async clickTabInNavigation(tabPosition: number): Promise<void> {
    if (tabPosition < 0) {
      throw new Error(
        `ERROR: Negative tab position, used tab position: ${tabPosition}`
      );
    }

    await this.page.locator(`div[role="tab"] >> nth=${tabPosition}`).click();
  }

  // Left navigation
  public async clickWorkflowsInNavigation(): Promise<void> {
    await this.page.locator('button:has-text("Workflows")').click();
    await this.page.waitForSelector('hd-navigation-category');
  }

  public async clickComponentsInNavigation(): Promise<void> {
    await this.page.locator('button:has-text("Components")').click();
    await this.page.waitForSelector('hd-navigation-category');
  }

  public async clickAddButtonInNavigation(buttonText: string): Promise<void> {
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
      .locator(`mat-expansion-panel:has-text("${categoryName}")`)
      .locator(`.navigation-item:has-text("${itemName}")`)
      .first()
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
      .locator(`mat-expansion-panel:has-text("${categoryName}")`)
      .locator(`.navigation-item:has-text("${itemName}")`)
      .first()
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
      .locator(`mat-expansion-panel:has-text("${categoryName}")`)
      .locator(`.navigation-item:has-text("${itemName}")`)
      .first()
      .click({ button: 'right' });
  }

  public async dragAndDropItemFromNavigationToFlowchart(
    categoryName: string,
    itemName: string
  ): Promise<void> {
    if (categoryName === '' || itemName === '') {
      throw new Error('ERROR: Category and item name must not be empty');
    }

    const source = this.page
      .locator(`mat-expansion-panel:has-text("${categoryName}")`)
      .locator(`.navigation-item:has-text("${itemName}")`)
      .first();

    const flowChartGrid = this.page.locator(
      'svg:has-text(".svg-small-grid { stroke: #a9a9a9; } .svg-grid { stroke: #a9a9a9; }") >> nth=0'
    );

    await source.dragTo(flowChartGrid);
  }

  public async clickOnContextMenu(menuItem: string): Promise<void> {
    if (menuItem === '') {
      throw new Error('ERROR: Menu item must not be empty');
    }

    await this.page
      .locator(`.mat-mdc-menu-content >> button:has-text("${menuItem}")`)
      .click();
  }

  public async searchInNavigation(searchTerm: string): Promise<void> {
    if (searchTerm === '') {
      throw new Error('ERROR: Search term must not be empty');
    }

    await this.page
      .locator('.navigation-container__search >> input')
      .pressSequentially(searchTerm);
  }

  public async clickIconInToolbar(iconTitle: string): Promise<void> {
    if (iconTitle === '') {
      throw new Error('ERROR: Icon title must not be empty');
    }

    await this.page
      .locator(`hd-toolbar >> mat-icon[title="${iconTitle}"]:not(.disabled)`)
      .click();
  }

  public async clickByTestId(testId: string): Promise<void> {
    if (testId === '') {
      throw new Error('ERROR: test id must not be empty');
    }

    await this.page.getByTestId(testId).click();
  }

  public async typeInInputByTestId(
    testId: string,
    inputText: string
  ): Promise<void> {
    if (testId === '' || inputText === '') {
      throw new Error('ERROR: test id or input text must not be empty');
    }

    // Select default input text and overwrite it
    const input = this.page.getByTestId(testId);
    await input.click();
    await input.press('Control+a');
    await input.pressSequentially(inputText);
  }

  public async typeInInputById(id: string, inputText: string): Promise<void> {
    if (id === '' || inputText === '') {
      throw new Error('ERROR: Id or input text must not be empty');
    }

    // Select default input text and overwrite it
    const input = this.page.locator(`input[id="${id}"]`);
    await input.click();
    await input.press('Control+a');
    await input.pressSequentially(inputText);

    // Workaround for autocomplete in create component / workflow dialog
    if (id === 'category') {
      // Tab out of input field to close suggested options
      await input.press('Tab');
    }
  }

  public async typeInDocumentationEditor(textareaText: string): Promise<void> {
    if (textareaText === '') {
      throw new Error('ERROR: Textarea text must not be empty');
    }

    const textArea = this.page.locator('hd-documentation-editor >> textarea');
    await textArea.click();
    await textArea.press('Control+a');
    await textArea.press('Delete');
    await textArea.pressSequentially(textareaText);
  }

  public async typeInJsonEditor(textareaText: string): Promise<void> {
    if (textareaText === '') {
      throw new Error('ERROR: Textarea text must not be empty');
    }

    const editorTextArea = this.page
      .locator('hd-json-editor >> .monaco-editor textarea')
      .first();
    await editorTextArea.press('Control+a');
    await editorTextArea.press('Delete');
    await editorTextArea.pressSequentially(textareaText);
  }

  public async typeInComponentEditor(
    pythonCode: string,
    removeCharsFromEnd: number = 0
  ): Promise<void> {
    if (pythonCode === '') {
      throw new Error('ERROR: Editor python code must not be empty');
    }
    if (removeCharsFromEnd < 0) {
      throw new Error(
        'ERROR: Cannot remove a negative number of chars from the end'
      );
    }

    // Textarea gets focus, remove old code from the end and insert new python code
    const editorTextArea = this.page
      .locator('hd-component-editor >> .monaco-editor >> textarea')
      .first();
    await this.page
      .locator('hd-component-editor >> .monaco-editor >> .view-line')
      .getByText('pass', { exact: true })
      .click();
    await editorTextArea.press('Control+a');
    await editorTextArea.press('End');

    for (let i = 0; i < removeCharsFromEnd; i++) {
      await editorTextArea.press('Backspace');
    }

    await editorTextArea.pressSequentially(pythonCode);
  }

  public async selectItemInDropdown(
    testId: string,
    itemText: string
  ): Promise<void> {
    if (testId === '' || itemText === '') {
      throw new Error('ERROR: Dropdown test id or item text must not be empty');
    }

    await this.page.getByTestId(testId).click();
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
      throw new Error('ERROR: From or to date must not be empty');
    }
    if (to.isBefore(from)) {
      throw new Error('To date must be after from date');
    }

    const timestampRange: Moment[] = [from, to];

    for (const timestamp of timestampRange) {
      // Choose year, month and day
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

      // Choose hours
      await this.page
        .locator('input[class="owl-dt-timer-input"] >> nth=0')
        .click();
      await this.page.press(
        'input[class="owl-dt-timer-input"] >> nth=0',
        'Control+a'
      );
      await this.page
        .locator('input[class="owl-dt-timer-input"] >> nth=0')
        .pressSequentially(timestamp.hours().toString());

      // Choose minutes
      await this.page
        .locator('input[class="owl-dt-timer-input"] >> nth=1')
        .click();
      await this.page.press(
        'input[class="owl-dt-timer-input"] >> nth=1',
        'Control+a'
      );
      await this.page
        .locator('input[class="owl-dt-timer-input"] >> nth=1')
        .pressSequentially(timestamp.minutes().toString());
    }

    await this.page
      .locator('owl-date-time-container >> button:has-text("Set")')
      .click();
  }
}
