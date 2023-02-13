import { ComponentPortal } from '@angular/cdk/portal';
import { Component, Input } from '@angular/core';
import { MatDialog } from '@angular/material/dialog';
import { select, Store } from '@ngrx/store';
import {
  createReadOnlyConfig,
  FlowchartConfiguration,
  SVGManipulatorConfiguration
} from 'hetida-flowchart';
import { timer } from 'rxjs';
import { first } from 'rxjs/operators';
import { BaseItemType } from 'src/app/enums/base-item-type';
import { RevisionState } from 'src/app/enums/revision-state';
import { ContextMenuService } from 'src/app/service/context-menu/context-menu.service';
import { PopoverService } from 'src/app/service/popover/popover.service';
import {
  selectAbstractBaseItemById,
  selectAbstractComponentBaseItems,
  selectAbstractWorkflowBaseItems
} from 'src/app/store/base-item/base-item.selectors';
import { v4 as UUID } from 'uuid';
import { popoverMinHeight, popoverWidth } from '../../constants/popover-sizes';
import { AbstractBaseItem, BaseItem } from '../../model/base-item';
import { IOItem } from '../../model/io-item';
import { WorkflowBaseItem } from '../../model/workflow-base-item';
import { WorkflowLink } from '../../model/workflow-link';
import { WorkflowOperator } from '../../model/workflow-operator';
import { NotificationService } from '../../service/notifications/notification.service';
import { FlowchartConverterService } from '../../service/type-converter/flowchart-converter.service';
import { WorkflowEditorService } from '../../service/workflow-editor/workflow-editor.service';
import { IAppState } from '../../store/app.state';
import { BaseItemContextMenuComponent } from '../base-item-context-menu/base-item-context-menu.component';
import {
  OperatorChangeRevisionDialogComponent,
  OperatorChangeRevisionDialogData
} from '../operator-change-revision-dialog/operator-change-revision-dialog.component';
import {
  RenameOperatorDialogComponent,
  RenameOperatorDialogData
} from '../rename-operator-dialog/rename-operator-dialog.component';

interface IdentifiableEntity {
  id: string;
}

@Component({
  selector: 'hd-workflow-editor',
  templateUrl: './workflow-editor.component.html',
  styleUrls: ['./workflow-editor.component.scss']
})
export class WorkflowEditorComponent {
  flowchartConfiguration: FlowchartConfiguration | undefined = undefined;
  flowchartManipulatorConfiguration: SVGManipulatorConfiguration = new SVGManipulatorConfiguration();

  private currentWorkflow: WorkflowBaseItem;
  private hasChanges = false;

  constructor(
    private readonly store: Store<IAppState>,
    private readonly notificationService: NotificationService,
    private readonly workflowService: WorkflowEditorService,
    private readonly flowchartConverter: FlowchartConverterService,
    private readonly popoverService: PopoverService,
    private readonly dialog: MatDialog,
    private readonly contextMenuService: ContextMenuService
  ) {
    // Only save updates every 500ms.
    timer(500, 500).subscribe(() => this._updateWorkflowIfNecessary());
  }

  @Input()
  set workflowBaseItem(workflowBaseItem: WorkflowBaseItem) {
    this._convertWorkflowToFlowchart(workflowBaseItem);
  }

  openContextMenu(mouseEvent: CustomEvent): void {
    const componentPortal = new ComponentPortal(BaseItemContextMenuComponent);
    const position = {
      y: mouseEvent.detail.mousePosition[1],
      x: mouseEvent.detail.mousePosition[0]
    };
    const { componentPortalRef } = this.contextMenuService.openContextMenu(
      componentPortal,
      position
    );
    componentPortalRef.instance.baseItem = this.currentWorkflow;
  }

  /**
   * handles updates to the workflow state
   * @param event event triggering the update
   */
  updatePosition(event: Event): void {
    const updatedElement = event.target as HTMLElement;
    if (updatedElement === null || updatedElement === undefined) {
      throw new Error('No element associated with the event!');
    }
    this._checkAndUpdateOperator(updatedElement);
    this._checkAndUpdateLink(updatedElement);
    this._checkAndUpdateInput(updatedElement);
    this._checkAndUpdateOutput(updatedElement);
  }

  /**
   * checks if the updated element was an operator, if yes we update it's position
   * @param element updated element
   */
  private _checkAndUpdateOperator(element: HTMLElement): void {
    const operator = this.currentWorkflow.operators.find(
      operatorCandidate => operatorCandidate.id === element.id
    );
    if (operator === undefined) {
      return;
    }
    this._updateOperatorPosition(element, operator);
  }

  /**
   * checks if the updated element was a link, if yes we update it's path if necessary
   * @param element updated element
   */
  private _checkAndUpdateLink(element: HTMLElement): void {
    const link = this.currentWorkflow.links.find(
      workflowLink => workflowLink.id === element.id
    );
    if (link === undefined) {
      return;
    }
    const pathData = this.flowchartConverter.convertLinkPathToPoints(element);
    if (link.path.length === 0 && pathData.length === 0) {
      return;
    }
    link.path = pathData;
    this.hasChanges = true;
  }

  /**
   * checks if the updated element was a workflow input, if yes we update it's position
   * @param element updated element
   */
  private _checkAndUpdateInput(element: HTMLElement): void {
    this._updateIoItem(element, this.currentWorkflow.inputs);
  }

  /**
   * checks if the updated element was a workflow output, if yes we update it's position
   * @param element updated element
   */
  private _checkAndUpdateOutput(element: HTMLElement): void {
    this._updateIoItem(element, this.currentWorkflow.outputs);
  }

  private _updateIoItem(element: HTMLElement, ioItems: IOItem[]) {
    const id = element.id.split('_')[1];
    const ioItem = ioItems.find(input => input.id === id);
    if (ioItem === undefined) {
      return;
    }
    ioItem.posX = Number(element.getAttribute('x'));
    ioItem.posY = Number(element.getAttribute('y'));
    this.hasChanges = true;
  }

  /**
   * handles removals from the workflow
   * @PerformanceCritical this happens synchronously to the removal, otherwise the element would be gone from the DOM
   * @param event event triggered by the removal
   */
  removeElement(event: Event): void {
    const removedElement = event.target as HTMLElement;
    if (removedElement === null || removedElement === undefined) {
      throw new Error('No element associated with the event!');
    }
    this.currentWorkflow.operators = this._removeById(
      this.currentWorkflow.operators,
      removedElement.id
    );
    this.currentWorkflow.inputs = this._removeById(
      this.currentWorkflow.inputs,
      removedElement.id
    );
    this.currentWorkflow.outputs = this._removeById(
      this.currentWorkflow.outputs,
      removedElement.id
    );
    this.currentWorkflow.links = this._removeById(
      this.currentWorkflow.links,
      removedElement.id
    );
    this.hasChanges = true;
  }

  private _removeById<T extends IdentifiableEntity>(
    sourceList: T[],
    id: string
  ): T[] {
    return sourceList.filter(
      identifiableEntity => identifiableEntity.id !== id
    );
  }

  private _removeOperatorLinks(
    links: WorkflowLink[],
    deletedOperator: WorkflowOperator
  ) {
    return links.filter(
      link =>
        !(
          link.fromOperator === deletedOperator.id ||
          link.toOperator === deletedOperator.id
        )
    );
  }

  /**
   * handles additions to the workflow
   * @param event event triggered by the addition
   */
  addElement(event: Event): void {
    const addedElement = event.target as HTMLElement;
    if (addedElement === null || addedElement === undefined) {
      throw new Error('No element associated with the event!');
    }
    this._checkAndAddOperator(addedElement);
    this._checkAndAddLink(addedElement);
  }

  /**
   * check if the operators is already set from the drop event, if yes update it's position
   * @param element added element
   */
  private _checkAndAddOperator(element: HTMLElement): void {
    if (element.getAttribute('dispatcher') !== 'operator') {
      return;
    }
    if (this.currentWorkflow.operators !== undefined) {
      const operator = this.currentWorkflow.operators.find(
        operatorCandidate => operatorCandidate.id === element.id
      );
      if (operator === undefined) {
        throw new Error(
          'Internal Error: Operator was not defined by drop event!'
        );
      }
      this._updateOperatorPosition(element, operator);
    }
  }

  /**
   * check if the link doesn't already exist, if not add it to the workflow
   * @param element link element
   */
  private _checkAndAddLink(element: HTMLElement): void {
    if (element.getAttribute('dispatcher') !== 'link') {
      return;
    }
    const link = this.currentWorkflow.links.find(
      wfLink => wfLink.id === element.id
    );
    if (link !== undefined) {
      return;
    }
    const linkSourceIds = this.flowchartConverter.getLinkOperatorAndConnector(
      element,
      true
    );
    const linkTargetIds = this.flowchartConverter.getLinkOperatorAndConnector(
      element,
      false
    );
    const linkPath = this.flowchartConverter.convertLinkPathToPoints(element);

    const newLink: WorkflowLink = {
      id: UUID().toString(),
      fromConnector: linkSourceIds.connectorId,
      fromOperator: linkSourceIds.operatorId,
      toConnector: linkTargetIds.connectorId,
      toOperator: linkTargetIds.operatorId,
      path: linkPath
    };
    this.currentWorkflow.links.push(newLink);
    element.id = newLink.id;
    this.hasChanges = true;
  }

  /**
   * adds a new operator to the workflow,
   * since the flowchart library doesn't need all the data we handle this here and not on the create event
   * @param event drop event, carrying the baseItem and flowchartComponent data
   */
  dropInterceptor(event: CustomEvent): void {
    if (event.detail.baseItemJSON === '') {
      return;
    }
    const baseItem = JSON.parse(event.detail.baseItemJSON) as BaseItem;
    const newOperator = this._createNewOperator(
      baseItem,
      event.detail.svgX as number,
      event.detail.svgY as number
    );
    this.currentWorkflow.operators.push(newOperator);
    this.workflowService.updateWorkflow(this.currentWorkflow);
  }

  /**
   * set selected element from workflow editor view to selection in sidebar
   * @param event activation event
   */
  setActive(event: Event): void {
    if (event.target === null) {
      return;
    }
    if (!(event.target instanceof SVGElement)) {
      return;
    }
    const target = event.target;
    const operator = this.currentWorkflow.operators.find(
      op => op.id === target.id
    );
    if (operator !== undefined) {
      const targetRect = target.getBoundingClientRect();
      const bodyRect = document.body.getBoundingClientRect();
      const openToRight = targetRect.right + popoverWidth < bodyRect.right;
      this.popoverService.showPopover(
        operator.itemId,
        openToRight ? targetRect.right : targetRect.left,
        targetRect.top,
        openToRight,
        false
      );
    } else if (target.nodeName === 'svg') {
      const position = (event as CustomEvent).detail;
      if (position === undefined) {
        this.popoverService.closePopover();
        return;
      }
      const bodyRect = document.body.getBoundingClientRect();
      const openToRight = position.x + popoverWidth < bodyRect.right;
      const openToTop = position.y + popoverMinHeight > bodyRect.bottom;
      this.popoverService.showPopover(
        this.currentWorkflow.id,
        position.x,
        openToTop ? position.y - popoverMinHeight : position.y,
        openToRight,
        false
      );
    } else {
      this.popoverService.closePopover();
    }
  }

  closePopover() {
    this.popoverService.closePopover();
  }

  /**
   * checks whether or not to open the revision change dialog
   * @param event event used to determine the targeted operator
   */
  changeRevision(event: Event): void {
    const currentOperator = this._extractCurrentOperatorFromEvent(event);
    if (!currentOperator) {
      return;
    }

    const selector =
      currentOperator.type === BaseItemType.WORKFLOW
        ? selectAbstractWorkflowBaseItems
        : selectAbstractComponentBaseItems;
    this.store
      .select(selector)
      .pipe(first())
      .subscribe(abstractBaseItems => {
        const available = abstractBaseItems.filter(
          abstractBaseItem =>
            abstractBaseItem.groupId === currentOperator.groupId &&
            abstractBaseItem.id !== currentOperator.itemId &&
            abstractBaseItem.state === RevisionState.RELEASED
        );

        if (available.length === 0) {
          this.notificationService.info(
            `This ${currentOperator.type.toLowerCase()} has no other revision.`
          );
        } else {
          this._openRevisionChangeDialog(available, currentOperator);
        }
      });
  }

  private _openRevisionChangeDialog(
    revisionList: AbstractBaseItem[],
    operator: WorkflowOperator
  ): void {
    const dialogRef = this.dialog.open<
      OperatorChangeRevisionDialogComponent,
      OperatorChangeRevisionDialogData,
      AbstractBaseItem | undefined
    >(OperatorChangeRevisionDialogComponent, {
      width: '640px',
      data: {
        revisions: revisionList
      }
    });
    dialogRef.afterClosed().subscribe(data => {
      if (data === undefined) {
        return;
      }
      const replacementWorkflowOperator = this._createNewOperator(
        data,
        operator.posX,
        operator.posY
      );

      const copyOfCurrentWorkflow = JSON.parse(
        JSON.stringify(this.currentWorkflow)
      ) as WorkflowBaseItem;

      // update workflow
      copyOfCurrentWorkflow.operators = this._removeById(
        copyOfCurrentWorkflow.operators,
        operator.id
      );
      copyOfCurrentWorkflow.links = this._removeOperatorLinks(
        copyOfCurrentWorkflow.links,
        operator
      );

      copyOfCurrentWorkflow.operators.push(replacementWorkflowOperator);
      this.workflowService.updateWorkflow(copyOfCurrentWorkflow);
    });
  }

  renameOperator(event: Event): void {
    const currentOperator = this._extractCurrentOperatorFromEvent(event);
    if (!currentOperator) {
      return;
    }
    this._openRenameOperatorDialog(currentOperator);
  }

  private _openRenameOperatorDialog(operator: WorkflowOperator): void {
    const dialogRef = this.dialog.open<
      RenameOperatorDialogComponent,
      RenameOperatorDialogData,
      string | undefined
    >(RenameOperatorDialogComponent, {
      width: '640px',
      data: {
        operator
      }
    });

    dialogRef.afterClosed().subscribe(data => {
      if (data === undefined) {
        return;
      }
      operator.name = data;
      this.workflowService.updateWorkflow(this.currentWorkflow);
      this._convertWorkflowToFlowchart(this.currentWorkflow);
    });
  }

  copyOperator(event: ClipboardEvent): void {
    const currentOperator = this._extractCurrentOperatorFromEvent(event);
    if (!currentOperator) {
      return;
    }
    this.store
      .pipe(select(selectAbstractBaseItemById(currentOperator.itemId)), first())
      .subscribe(abstractBaseItem => {
        const copyOperator = this._createNewOperator(
          abstractBaseItem,
          currentOperator.posX + 100,
          currentOperator.posY + 100
        );
        this.currentWorkflow.operators.push(copyOperator);
        this.workflowService.updateWorkflow(this.currentWorkflow);
      });
  }

  private _extractCurrentOperatorFromEvent(
    event: Event
  ): WorkflowOperator | null {
    const element = event.target as HTMLElement;
    if (element === null) {
      return null;
    }
    const currentOperator = this.currentWorkflow.operators.find(
      operator => operator.id === element.id
    );
    if (
      currentOperator === undefined ||
      (currentOperator.type !== BaseItemType.WORKFLOW &&
        currentOperator.type !== BaseItemType.COMPONENT)
    ) {
      throw new Error('Invalid operator');
    }
    return currentOperator;
  }

  private _updateWorkflowIfNecessary(): void {
    if (!this.hasChanges || this.currentWorkflow.state === 'RELEASED') {
      return;
    }
    this.workflowService.updateWorkflow(this.currentWorkflow);
    this.hasChanges = false;
  }

  private _convertWorkflowToFlowchart(workflow: WorkflowBaseItem): void {
    if (workflow.state === RevisionState.RELEASED) {
      this.flowchartManipulatorConfiguration = createReadOnlyConfig(
        this.flowchartManipulatorConfiguration
      );
    }
    this.flowchartManipulatorConfiguration.dispatchContextMenuEvent = true;
    this.flowchartConfiguration = this.flowchartConverter.convertWorkflowToFlowchart(
      workflow
    );
    this.currentWorkflow = workflow;
    if (
      this.currentWorkflow.operators.some(
        operator => operator.state === RevisionState.DISABLED
      )
    ) {
      // https://github.com/angular/angular/issues/15634#issuecomment-345504902
      setTimeout(() =>
        this.notificationService.warn(
          'This workflow contains disabled components! Consider updating them to a newer revision!'
        )
      );
    }
  }

  /**
   * creates a new workflow operator based on the base item and flowchart data
   * @param abstractBaseItem base item definition
   * @param posX x co-ordinate of the operator
   * @param posY y co-ordinate of the operator
   */
  private _createNewOperator(
    abstractBaseItem: AbstractBaseItem,
    posX: number,
    posY: number
  ): WorkflowOperator {
    const newOperator: WorkflowOperator = {
      ...abstractBaseItem,
      itemId: abstractBaseItem.id,
      posY,
      posX,
      id: UUID().toString()
    };
    const sameBaseItems = this.currentWorkflow.operators.filter(
      workflowOperator => workflowOperator.itemId === newOperator.itemId
    );
    if (sameBaseItems.length > 0) {
      newOperator.name = `${newOperator.name} (${sameBaseItems.length + 1})`;
    }
    return newOperator;
  }

  private _updateOperatorPosition(
    element: HTMLElement,
    operator: WorkflowOperator
  ) {
    const newPosX = Number(element.getAttribute('x'));
    const newPosY = Number(element.getAttribute('y'));
    if (operator.posX !== newPosX || operator.posY !== newPosY) {
      operator.posX = newPosX;
      operator.posY = newPosY;
      this.hasChanges = true;
    }
  }
}
