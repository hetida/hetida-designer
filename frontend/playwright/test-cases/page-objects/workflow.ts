import { Page, expect } from '@playwright/test';
import { Navigation } from './navigation';
import { ErrorNotification } from './error-notification';

export class Workflow {
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

  public async addWorkflow(
    categoryName: string,
    workflowName: string
  ): Promise<void> {}

  public async openWorkflow(
    categoryName: string,
    workflowName: string
  ): Promise<void> {
    await this.navigation.clickBtnNavigation('Workflows');

    // Expansion-panel expands on click
    await this.navigation.clickExpansionPanelNavigation(categoryName);

    const visibleExpansionPanelContent = this.page
      .locator(`mat-expansion-panel:has-text("${categoryName}") >> nth=0`)
      .locator('.mat-expansion-panel-content');
    await expect(visibleExpansionPanelContent).toBeVisible();

    // Hover over workflow, check if error-notification occurred
    await this.navigation.hoverItemNavigation(categoryName, workflowName);
    const countErrorNotification = await this.errorNotification.checkErrorNotification();
    expect(countErrorNotification).toEqual(0);

    // Open workflow on double-click
    await this.navigation.doubleClickItemNavigation(categoryName, workflowName);

    // Check for equal names in list and opened tab
    const workflowListName = await this.page
      .locator(`mat-expansion-panel:has-text("${categoryName}") >> nth=0`)
      .locator(`.navigation-item:has-text("${workflowName}") >> nth=0`)
      .locator('.text-ellipsis')
      .innerText();
    const workflowTabName = await this.page
      .locator('div[role="tab"] >> nth=1')
      .locator('.text-ellipsis')
      .innerText();
    expect(workflowListName).toEqual(workflowTabName);

    // Check if hd-workflow-editor exists and contains a svg image
    const svgInEditor = this.page
      .locator('hd-workflow-editor')
      .locator('svg >> nth=0');
    await expect(svgInEditor).toHaveAttribute('class', 'hetida-flowchart-svg');
  }

  public async declareWorkflow(
    categoryName: string,
    workflowName: string
  ): Promise<void> {}

  public async editWorkflow(
    categoryName: string,
    workflowName: string
  ): Promise<void> {}

  public async executeWorkflow(
    categoryName: string,
    workflowName: string
  ): Promise<void> {
    await this.navigation.clickBtnNavigation('Workflows');
    // Expansion-panel expands on click
    await this.navigation.clickExpansionPanelNavigation(categoryName);
    // Open workflow on double-click
    await this.navigation.doubleClickItemNavigation(categoryName, workflowName);

    // Execute workflow, click on icon "Execute"
    await this.navigation.clickIconToolbar('Execute');

    // Check if execute workflow dialog-container exists
    await this.page.waitForSelector('mat-dialog-container'); // Wait for dialog-container
    const countDialogContainer = await this.page
      .locator('mat-dialog-container')
      .count();
    expect(countDialogContainer).toEqual(1);

    // Check for equal substrings in dialog-title and opened tab
    const dialogTitle = this.page.locator('.mat-dialog-title h4');
    const workflowTabName = await this.page
      .locator('div[role="tab"] >> nth=1')
      .locator('.text-ellipsis')
      .innerText();
    await expect(dialogTitle).toContainText(`${workflowTabName}`);

    // Confirm execute workflow, click on button "Execute"
    await this.navigation.clickBtnDialog('Execute');

    // Check if error-notification occurred
    const countErrorNotification = await this.errorNotification.checkErrorNotification();
    expect(countErrorNotification).toEqual(0);

    // Check if hd-protocol-viewer is visible
    const visibleProtocolViewer = this.page.locator('hd-protocol-viewer');
    await expect(visibleProtocolViewer).toBeVisible();

    // Check if plotly-plot exist in hd-protocol-viewer
    await this.page.waitForSelector('hd-protocol-viewer >> plotly-plot'); // Wait for plotly-plot

    const countPlotlyPlot = await this.page
      .locator('hd-protocol-viewer >> plotly-plot')
      .count();
    expect(countPlotlyPlot).toBeGreaterThan(0);
  }

  public async deleteWorkflow(
    categoryName: string,
    workflowName: string
  ): Promise<void> {}
}
