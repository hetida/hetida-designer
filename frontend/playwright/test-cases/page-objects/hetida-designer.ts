import { BrowserContext, Page, expect } from '@playwright/test';
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

  // TODO: use test ids
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
    await this.page.getByTestId('workflows-navigation-container').click();
    await this.page.waitForSelector('hd-navigation-category');
  }

  public async clickComponentsInNavigation(): Promise<void> {
    await this.page.getByTestId('components-navigation-container').click();
    await this.page.waitForSelector('hd-navigation-category');
  }

  public async clickAddButtonInNavigation(buttonText: string): Promise<void> {
    if (buttonText === '') {
      throw new Error('ERROR: Button text must not be empty');
    }

    await this.page
      .getByTestId(`${buttonText.toLowerCase()}-navigation-container`)
      .click();
    await this.page.waitForSelector('mat-dialog-container');
  }

  /**
   * Makes sure a category in the navigation is expanded - it does not simply
   * click it.
   *
   * The expansion panel header toggles, so clicking a category that is already
   * open collapses it again, and the wait for its content then runs into the
   * timeout. Which state it starts in is not always obvious: a search filter
   * can rebuild the list, and a test may have expanded the category earlier.
   * The click is also retried, in case it lands while the list is still
   * rendering and the header is replaced underneath it.
   */
  public async clickCategoryInNavigation(categoryName: string): Promise<void> {
    if (categoryName === '') {
      throw new Error('ERROR: Category name must not be empty');
    }

    const header = this.page.getByTestId(
      `${categoryName.toLowerCase()}-navigation-category`
    );
    const firstItem = this.page
      .getByTestId(
        `${categoryName.toLowerCase()}-expansion-panel-navigation-category`
      )
      .first();

    await expect(async () => {
      if ((await header.getAttribute('aria-expanded')) !== 'true') {
        await header.click();
      }
      await expect(firstItem).toBeVisible({ timeout: 5000 });
    }).toPass({ timeout: 30000 });
  }

  public async hoverItemInNavigation(itemName: string): Promise<void> {
    if (itemName === '') {
      throw new Error('ERROR: Item name must not be empty');
    }

    await this.page
      .getByTestId(`${itemName.toLowerCase()}-navigation-item`)
      .first()
      .hover();
  }

  /**
   * Opens a navigation item in a tab by double clicking it.
   *
   * The double click is retried until a tab really appears. The item is a
   * plain element with a native (dblclick) handler and draggable="true", and
   * when the machine is busy firefox does not always turn the two clicks into
   * a dblclick - they arrive too far apart, or a stray drag swallows them.
   * Nothing throws when that happens: the click succeeds, no tab opens, and
   * whatever the test does next waits for an editor that never appears.
   */
  public async doubleClickItemInNavigation(itemName: string): Promise<void> {
    if (itemName === '') {
      throw new Error('ERROR: Item name must not be empty');
    }

    const item = this.page
      .getByTestId(`${itemName.toLowerCase()}-navigation-item`)
      .first();
    const tabs = this.page.locator('div[role="tab"]');
    const tabsBefore = await tabs.count();

    await expect(async () => {
      if ((await tabs.count()) === tabsBefore) {
        await item.dblclick();
      }
      await expect(tabs).not.toHaveCount(tabsBefore, { timeout: 3000 });
    }).toPass({ timeout: 30000 });
  }

  /**
   * Right clicks a navigation item and waits for its context menu.
   *
   * The click is retried: in firefox the first right click on a freshly
   * rendered navigation item sometimes does not open the menu at all
   * (reproduced about one run in six). Waiting for a menu that is never coming
   * burns the whole test timeout, and the cleanup hooks that used to call this
   * then left their transformation behind.
   */
  public async rightClickItemInNavigation(itemName: string): Promise<void> {
    if (itemName === '') {
      throw new Error('ERROR: Item name must not be empty');
    }

    const item = this.page
      .getByTestId(`${itemName.toLowerCase()}-navigation-item`)
      .first();
    const contextMenu = this.page.locator('.mat-mdc-menu-panel');

    await expect(async () => {
      if ((await contextMenu.count()) === 0) {
        await item.click({ button: 'right' });
      }
      await expect(contextMenu).toHaveCount(1);
    }).toPass({ timeout: 20000 });
  }

  public async dragAndDropItemFromNavigationToFlowchart(
    itemName: string
  ): Promise<void> {
    if (itemName === '') {
      throw new Error('ERROR: Item name must not be empty');
    }

    const source = this.page
      .getByTestId(`${itemName.toLowerCase()}-navigation-item`)
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

    const inputSearch = this.page.getByTestId('search-navigation-container');
    await inputSearch.click();
    await inputSearch.press('Control+a');
    await inputSearch.pressSequentially(searchTerm);
  }

  public async clickIconInToolbar(dataTestId: string): Promise<void> {
    if (dataTestId === '') {
      throw new Error('ERROR: dataTestId must not be empty');
    }

    await this.page
      .locator(
        `hd-toolbar >> mat-icon[data-testid="${dataTestId}"]:not(.disabled)`
      )
      .click();
  }

  /**
   * Clicks Execute in the toolbar and waits for the wiring dialog to show up.
   *
   * The click is retried on purpose. The toolbar only marks Execute as
   * disabled while its `incompleteFlag` says so, and
   * TransformationActionService.execute() returns without any feedback when
   * the transformation is not loaded yet - so a click that lands too early is
   * swallowed silently. Just waiting for the dialog would burn the whole test
   * timeout instead of clicking again.
   */
  public async openExecuteDialog(dialogTitle?: string): Promise<void> {
    const dialog =
      dialogTitle === undefined
        ? this.page.locator('mat-dialog-container')
        : this.page.locator(`mat-dialog-container:has-text("${dialogTitle}")`);

    await expect(async () => {
      if ((await dialog.count()) === 0) {
        await this.clickIconInToolbar('Execute');
      }
      await expect(dialog.first()).toBeVisible({ timeout: 5000 });
    }).toPass({ timeout: 30000 });
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

  public async typeInJsonEditor(
    textareaText: string,
    browserName: string
  ): Promise<void> {
    if (textareaText === '') {
      throw new Error('ERROR: Textarea text must not be empty');
    }

    const editorTextArea = this.page
      .locator('hd-json-editor >> .monaco-editor textarea')
      .first();
    await editorTextArea.press('Control+a');
    await editorTextArea.press('Delete');

    if (browserName === 'firefox') {
      await editorTextArea.pressSequentially(textareaText);
    } else {
      await editorTextArea.fill(textareaText);
    }
  }

  /**
   * Replaces the `pass` placeholder in the component editor with the given code.
   *
   * Selects the placeholder instead of deleting a fixed number of characters
   * from the end of the document: that depended on what the generated code
   * happens to end with, and quietly wrote the code into the wrong place when
   * it did not. Monaco's Home stops at the first non-whitespace character, so
   * the indentation of the line survives.
   *
   * The caller has to make sure the editor already shows the code generated for
   * the current io interface - see components-create.spec.ts. Configuring
   * inputs and outputs makes the backend regenerate the code and the editor
   * reload it, and anything typed before that lands is thrown away.
   */
  public async typeInComponentEditor(pythonCode: string): Promise<void> {
    if (pythonCode === '') {
      throw new Error('ERROR: Editor python code must not be empty');
    }

    const editor = this.page.locator('hd-component-editor >> .monaco-editor');
    const placeholder = this.page
      .locator('hd-component-editor >> .monaco-editor >> .view-line')
      .getByText('pass', { exact: true });

    // Monaco only renders the lines it is showing, and the generated code is
    // long enough that the placeholder starts out below the fold - where it is
    // not in the dom at all, so it cannot be clicked or scrolled into view.
    await editor.first().hover();
    await expect(async () => {
      if ((await placeholder.count()) === 0) {
        await this.page.mouse.wheel(0, 200);
      }
      await expect(placeholder).toHaveCount(1);
    }).toPass({ timeout: 15000 });

    await placeholder.click();

    const editorTextArea = this.page
      .locator('hd-component-editor >> .monaco-editor >> textarea')
      .first();

    // Home stops at the first non-whitespace character, so this selects the
    // placeholder without its indentation.
    await editorTextArea.press('End');
    await editorTextArea.press('Shift+Home');
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
