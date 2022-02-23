import { Page, expect } from '@playwright/test';
import { Navigation } from './navigation';
import { ErrorNotification } from './error-notification';

export class Component {
  private readonly page: Page;
  private readonly navigation: Navigation;
  private readonly errorNotification: ErrorNotification;

  constructor(
    page: Page,
    navigation: Navigation,
    errorNotification: ErrorNotification
  ) {
    this.page = page;
    this.navigation = navigation;
    this.errorNotification = errorNotification;
  }

  public async addComponent(
    categoryName: string,
    componentName: string,
    shortDescription: string,
    tag: string
  ): Promise<void> {
    await this.navigation.clickBtnNavigation('Components');
    await this.navigation.clickBtnNavigation('Add component');

    // Check if create component dialog-container exists
    await this.page.waitForSelector('mat-dialog-container'); // Wait for dialog-container
    const countDialogContainer = await this.page
      .locator('mat-dialog-container')
      .count();
    expect(countDialogContainer).toEqual(1);

    // Type in component details
    await this.navigation.typeInInputDialog('name', componentName); // Component name
    await this.navigation.typeInInputDialog('category', categoryName); // Category
    await this.navigation.typeInInputDialog('description', shortDescription); // Short description
    await this.navigation.typeInInputDialog('tag', tag); // Tag

    // Click on "Create Component"
    await this.navigation.clickBtnDialog('Create Component');
  }

  public async openComponent(
    categoryName: string,
    componentName: string
  ): Promise<void> {
    await this.navigation.clickBtnNavigation('Components');

    // Expansion-panel expands on click
    await this.navigation.clickExpansionPanelNavigation(categoryName);

    const visibleExpansionPanelContent = this.page
      .locator(`mat-expansion-panel:has-text("${categoryName}") >> nth=0`)
      .locator('.mat-expansion-panel-content');
    await expect(visibleExpansionPanelContent).toBeVisible();

    // Hover over component, check if error-notification occurred
    await this.navigation.hoverItemNavigation(categoryName, componentName);
    await this.errorNotification.checkErrorNotification();

    // Open component on double-click
    await this.navigation.doubleClickItemNavigation(
      categoryName,
      componentName
    );

    // Check for equal names in list and opened tab
    const componentListName = await this.page
      .locator(`mat-expansion-panel:has-text("${categoryName}") >> nth=0`)
      .locator(`.navigation-item:has-text("${componentName}") >> nth=0`)
      .locator('.text-ellipsis')
      .innerText();
    const componentTabName = await this.page
      .locator('div[role="tab"] >> nth=1')
      .locator('.text-ellipsis')
      .innerText();
    expect(componentListName).toEqual(componentTabName);

    // Check if hd-component-editor exists
    const countComponentEditor = await this.page
      .locator('hd-component-editor')
      .count();
    expect(countComponentEditor).toEqual(1);
  }

  public async declareComponent(
    categoryName: string,
    componentName: string
  ): Promise<void> {}

  public async editComponent(
    categoryName: string,
    componentName: string
  ): Promise<void> {}

  public async executeComponent(
    categoryName: string,
    componentName: string
  ): Promise<void> {
    await this.navigation.clickBtnNavigation('Components');
    // Expansion-panel expands on click
    await this.navigation.clickExpansionPanelNavigation(categoryName);
    // Open component on double-click
    await this.navigation.doubleClickItemNavigation(
      categoryName,
      componentName
    );

    // Execute component, click on icon "Execute"
    await this.navigation.clickIconToolbar('Execute');

    // Check if execute component dialog-container exists
    await this.page.waitForSelector('mat-dialog-container'); // Wait for dialog-container
    const countDialogContainer = await this.page
      .locator('mat-dialog-container')
      .count();
    expect(countDialogContainer).toEqual(1);

    // Check for equal substrings in dialog-title and opened tab
    const dialogTitle = this.page.locator('.mat-dialog-title h4');
    const componentTabName = await this.page
      .locator('div[role="tab"] >> nth=1')
      .locator('.text-ellipsis')
      .innerText();
    await expect(dialogTitle).toContainText(`${componentTabName}`);

    // Confirm execute component, click on button "Execute"
    await this.navigation.clickBtnDialog('Execute');

    // Check if error-notification occurred
    await this.errorNotification.checkErrorNotification();

    // Check if hd-protocol-viewer is visible
    const visibleProtocolViewer = this.page.locator('hd-protocol-viewer');
    await expect(visibleProtocolViewer).toBeVisible();
    // Check if hd-protocol-viewer contains a result
    await expect(visibleProtocolViewer).not.toBeEmpty();
  }

  public async deleteComponent(
    categoryName: string,
    componentName: string
  ): Promise<void> {}
}
