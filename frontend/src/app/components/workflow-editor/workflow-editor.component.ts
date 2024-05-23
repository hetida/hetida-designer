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
import { TransformationType } from 'src/app/enums/transformation-type';
import { RevisionState } from 'src/app/enums/revision-state';
import { ContextMenuService } from 'src/app/service/context-menu/context-menu.service';
import { PopoverService } from 'src/app/service/popover/popover.service';
import { v4 as UUID } from 'uuid';
import { popoverMinHeight, popoverWidth } from '../../constants/popover-sizes';
import { NotificationService } from '../../service/notifications/notification.service';
import { FlowchartConverterService } from '../../service/type-converter/flowchart-converter.service';
import { TransformationContextMenuComponent } from '../transformation-context-menu/transformation-context-menu.component';
import {
  OperatorChangeRevisionDialogComponent,
  OperatorChangeRevisionDialogData
} from '../operator-change-revision-dialog/operator-change-revision-dialog.component';
import {
  RenameOperatorDialogComponent,
  RenameOperatorDialogData
} from '../rename-operator-dialog/rename-operator-dialog.component';
import {
  Transformation,
  WorkflowTransformation
} from '../../model/transformation';
import { Link } from 'src/app/model/link';
import { Operator } from 'src/app/model/operator';
import { IOConnector } from 'src/app/model/io-connector';
import { TransformationState } from 'src/app/store/transformation/transformation.state';
import {
  selectAllTransformations,
  selectTransformationById
} from 'src/app/store/transformation/transformation.selectors';
import { TransformationService } from 'src/app/service/transformation/transformation.service';
import { Connector } from 'src/app/model/connector';
import { Utils } from 'src/app/utils/utils';
import { Constant } from 'src/app/model/constant';
import { OptionalFieldsDialogComponent } from '../optional-fields-dialog/optional-fields-dialog.component';

interface IdentifiableEntity {
  id: string;
}

export interface VertexIds {
  operatorId: string;
  connectorId: string;
}

@Component({
  selector: 'hd-workflow-editor',
  templateUrl: './workflow-editor.component.html',
  styleUrls: ['./workflow-editor.component.scss']
})
export class WorkflowEditorComponent {
  flowchartConfiguration: FlowchartConfiguration | undefined = undefined;
  flowchartManipulatorConfiguration: SVGManipulatorConfiguration =
    new SVGManipulatorConfiguration();

  private currentWorkflow: WorkflowTransformation;
  private hasChanges = false;

  constructor(
    private readonly transformationStore: Store<TransformationState>,
    private readonly notificationService: NotificationService,
    private readonly transformationService: TransformationService,
    private readonly flowchartConverter: FlowchartConverterService,
    private readonly popoverService: PopoverService,
    private readonly dialog: MatDialog,
    private readonly contextMenuService: ContextMenuService
  ) {
    // Only save updates every 500ms.
    timer(500, 500).subscribe(() => this._updateWorkflowIfNecessary());
  }

  @Input()
  set workflowTransformation(workflowTransformation: WorkflowTransformation) {
    this._convertWorkflowToFlowchart(workflowTransformation);
  }

  openContextMenu(mouseEvent: CustomEvent): void {
    const componentPortal = new ComponentPortal(
      TransformationContextMenuComponent
    );
    const position = {
      y: mouseEvent.detail.mousePosition[1],
      x: mouseEvent.detail.mousePosition[0]
    };
    const { componentPortalRef } = this.contextMenuService.openContextMenu(
      componentPortal,
      position
    );
    componentPortalRef.instance.transformation = this.currentWorkflow;
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
    const operator = this.currentWorkflow.content.operators.find(
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
    const link = this.currentWorkflow.content.links.find(
      workflowLink => workflowLink.id === element.id
    );
    if (link === undefined) {
      return;
    }
    const pathData =
      this.flowchartConverter.convertLinkPathToPositions(element);
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
    this._updateIoItem(element, this.currentWorkflow.content.inputs);
  }

  /**
   * checks if the updated element was a workflow output, if yes we update it's position
   * @param element updated element
   */
  private _checkAndUpdateOutput(element: HTMLElement): void {
    this._updateIoItem(element, this.currentWorkflow.content.outputs);
  }

  private _updateIoItem(element: HTMLElement, ioConnectors: IOConnector[]) {
    const id = element.id.split('_')[1];
    const ioConnector = ioConnectors.find(input => input.id === id);
    if (ioConnector === undefined) {
      return;
    }
    ioConnector.position.x = Number(element.getAttribute('x'));
    ioConnector.position.y = Number(element.getAttribute('y'));
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
    this.currentWorkflow.content.operators = this._removeById(
      this.currentWorkflow.content.operators,
      removedElement.id
    );
    this.currentWorkflow.content.inputs = this._removeById(
      this.currentWorkflow.content.inputs,
      removedElement.id
    );
    this.currentWorkflow.content.outputs = this._removeById(
      this.currentWorkflow.content.outputs,
      removedElement.id
    );
    this.currentWorkflow.content.links = this._removeById(
      this.currentWorkflow.content.links,
      removedElement.id
    );
    this.currentWorkflow.content.constants =
      this.currentWorkflow.content.constants.filter(
        constant => constant.operator_id !== removedElement.id
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

  private _removeOperatorLinks(links: Link[], deletedOperator: Operator) {
    return links.filter(
      link =>
        !(
          link.start.operator === deletedOperator.id ||
          link.end.operator === deletedOperator.id
        )
    );
  }

  private _removeOperatorConstants(
    constants: Constant[],
    deletedOperator: Operator
  ) {
    return constants.filter(
      constant => constant.operator_id !== deletedOperator.id
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
    if (this.currentWorkflow.content.operators !== undefined) {
      const operator = this.currentWorkflow.content.operators.find(
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
    const link = this.currentWorkflow.content.links.find(
      wfLink => wfLink.id === element.id
    );
    if (link !== undefined) {
      return;
    }

    const linkSourceIds: VertexIds =
      this.flowchartConverter.getLinkOperatorAndConnectorId(element, true);
    const linkTargetIds: VertexIds =
      this.flowchartConverter.getLinkOperatorAndConnectorId(element, false);

    const sourceIsWorkflowInput =
      linkSourceIds.operatorId === this.currentWorkflow.id;
    const startConnector: Connector =
      this.flowchartConverter.getConnectorFromOperatorById(
        linkSourceIds,
        this.currentWorkflow,
        sourceIsWorkflowInput
      );

    const targetIsWorkflowOutput =
      linkTargetIds.operatorId === this.currentWorkflow.id;
    const endConnector: Connector =
      this.flowchartConverter.getConnectorFromOperatorById(
        linkTargetIds,
        this.currentWorkflow,
        targetIsWorkflowOutput
      );

    const linkPath =
      this.flowchartConverter.convertLinkPathToPositions(element);

    const newLink: Link = {
      id: UUID().toString(),
      start: {
        operator: linkSourceIds.operatorId,
        connector: startConnector
      },
      end: {
        operator: linkTargetIds.operatorId,
        connector: endConnector
      },
      path: linkPath
    };

    this.currentWorkflow.content.links.push(newLink);
    element.id = newLink.id;
    this.hasChanges = true;
  }

  /**
   * adds a new operator and ioConnectors to the workflow,
   * since the flowchart library doesn't need all the data we handle this here and not on the create event
   * @param event drop event, carrying the transformation and flowchartComponent data
   */
  dropInterceptor(event: CustomEvent): void {
    if (event.detail.transformationJSON === '') {
      return;
    }
    const transformation = JSON.parse(
      event.detail.transformationJSON
    ) as Transformation;

    const newOperator = this._createNewOperator(
      transformation,
      event.detail.svgX as number,
      event.detail.svgY as number
    );
    this.currentWorkflow.content.operators.push(newOperator);
    this.transformationService
      .updateTransformation(this.currentWorkflow)
      .subscribe();
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
    const operator = this.currentWorkflow.content.operators.find(
      op => op.id === target.id
    );
    if (operator !== undefined) {
      const targetRect = target.getBoundingClientRect();
      const bodyRect = document.body.getBoundingClientRect();
      const openToRight = targetRect.right + popoverWidth < bodyRect.right;
      this.popoverService.showPopover(
        operator.transformation_id,
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
      const openToRight =
        (position.x as number) + popoverWidth < bodyRect.right;
      const openToTop =
        (position.y as number) + popoverMinHeight > bodyRect.bottom;
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

    this.transformationStore
      .select(selectAllTransformations)
      .pipe(first())
      .subscribe(transformations => {
        const revisions = transformations.filter(
          transformation =>
            transformation.revision_group_id ===
              currentOperator.revision_group_id &&
            transformation.id !== currentOperator.transformation_id &&
            transformation.state === RevisionState.RELEASED
        );

        if (revisions.length === 0) {
          this.notificationService.info(
            `This ${currentOperator.type.toLowerCase()} has no other revision.`
          );
        } else {
          this._openRevisionChangeDialog(revisions, currentOperator);
        }
      });
  }

  private _openRevisionChangeDialog(
    revisionList: Transformation[],
    operator: Operator
  ): void {
    const dialogRef = this.dialog.open<
      OperatorChangeRevisionDialogComponent,
      OperatorChangeRevisionDialogData,
      Transformation | undefined
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
      const replacementOperator = this._createNewOperator(
        data,
        operator.position.x,
        operator.position.y
      );

      const copyOfCurrentWorkflow = Utils.deepCopy(this.currentWorkflow);

      // update workflow
      copyOfCurrentWorkflow.content.operators = this._removeById(
        copyOfCurrentWorkflow.content.operators,
        operator.id
      );
      copyOfCurrentWorkflow.content.links = this._removeOperatorLinks(
        copyOfCurrentWorkflow.content.links,
        operator
      );
      copyOfCurrentWorkflow.content.constants = this._removeOperatorConstants(
        copyOfCurrentWorkflow.content.constants,
        operator
      );

      copyOfCurrentWorkflow.content.operators.push(replacementOperator);
      this.transformationService
        .updateTransformation(copyOfCurrentWorkflow)
        .subscribe();
    });
  }

  renameOperator(event: Event): void {
    const currentOperator = this._extractCurrentOperatorFromEvent(event);
    if (!currentOperator) {
      return;
    }
    this._openRenameOperatorDialog(currentOperator);
  }

  private _openRenameOperatorDialog(operator: Operator): void {
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

    dialogRef.afterClosed().subscribe(newName => {
      if (newName === undefined) {
        return;
      }
      operator.name = newName;
      this.transformationService
        .updateTransformation(this.currentWorkflow)
        .subscribe();
    });
  }

  copyOperator(event: ClipboardEvent): void {
    const currentOperator = this._extractCurrentOperatorFromEvent(event);
    if (!currentOperator) {
      return;
    }
    this.transformationStore
      .pipe(
        select(selectTransformationById(currentOperator.transformation_id)),
        first()
      )
      .subscribe(transformation => {
        const copyOperator = this._createNewOperator(
          transformation,
          currentOperator.position.x + 100,
          currentOperator.position.y + 100
        );
        this.currentWorkflow.content.operators.push(copyOperator);
        this.transformationService
          .updateTransformation(this.currentWorkflow)
          .subscribe();
      });
  }

  showOptionalFields(event: CustomEvent): void {
    const uuid = event.detail.uuid;
    if (uuid) {
      const selected_op = this.currentWorkflow.content.operators.filter(
        op => op.id === event.detail.uuid
      )[0];
      if (selected_op) {
        const dialogRef = this.dialog.open<OptionalFieldsDialogComponent>(
          OptionalFieldsDialogComponent,
          {
            width: '30%',
            minHeight: '200px',
            data: {
              operator: selected_op,
              actionOk: 'Save',
              actionCancel: 'Cancel'
            }
          }
        );

        dialogRef
          .afterClosed()
          .pipe(first())
          .subscribe((inputs: Connector[]) => {
            if (inputs) {
              this.currentWorkflow.content.operators.filter(
                op => op.id === event.detail.uuid
              )[0].inputs = inputs;
              inputs
                .filter(input => !input.exposed)
                .forEach(input => {
                  this.currentWorkflow.content.inputs
                    .filter(
                      contentInput =>
                        contentInput.operator_id === event.detail.uuid
                    )
                    .filter(filterInput => {
                      if (filterInput.connector_id === input.id) {
                        filterInput.name = '';
                      }
                    });
                });
              this.hasChanges = true;
              this._updateWorkflowIfNecessary();
            }
          });
      }
    } else {
      console.error('No UUID send from flowchart event!');
    }
  }

  private _extractCurrentOperatorFromEvent(event: Event): Operator | null {
    const element = event.target as HTMLElement;
    if (element === null) {
      return null;
    }
    const currentOperator = this.currentWorkflow.content.operators.find(
      operator => operator.id === element.id
    );
    if (
      currentOperator === undefined ||
      (currentOperator.type !== TransformationType.WORKFLOW &&
        currentOperator.type !== TransformationType.COMPONENT)
    ) {
      throw new Error('Invalid operator');
    }
    return currentOperator;
  }

  private _updateWorkflowIfNecessary(): void {
    if (
      !this.hasChanges ||
      this.currentWorkflow.state === RevisionState.RELEASED
    ) {
      return;
    }
    this.transformationService
      .updateTransformation(this.currentWorkflow)
      .subscribe(() => (this.hasChanges = false));
  }

  private _convertWorkflowToFlowchart(workflow: WorkflowTransformation): void {
    if (workflow.state === RevisionState.RELEASED) {
      this.flowchartManipulatorConfiguration = createReadOnlyConfig(
        this.flowchartManipulatorConfiguration
      );
    }
    this.flowchartManipulatorConfiguration.dispatchContextMenuEvent = true;
    this.flowchartConfiguration =
      this.flowchartConverter.convertWorkflowToFlowchart(workflow);

    this.currentWorkflow = workflow;

    if (
      this.currentWorkflow.content.operators.some(
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
   * creates a new workflow operator based on the transformation and flowchart data
   * @param transformation transformation definition
   * @param posX x co-ordinate of the operator
   * @param posY y co-ordinate of the operator
   */
  private _createNewOperator(
    transformation: Transformation,
    posX: number,
    posY: number
  ): Operator {
    const newOperator: Operator = {
      ...transformation,
      id: UUID().toString(),
      transformation_id: transformation.id,
      inputs: transformation.io_interface.inputs.map(input => ({
        ...input,
        position: { x: 0, y: 0 }
      })),
      outputs: transformation.io_interface.outputs.map(output => ({
        ...output,
        position: { x: 0, y: 0 }
      })),
      position: { x: posX, y: posY }
    };
    const sameOperator = this.currentWorkflow.content.operators.filter(
      workflowOperator =>
        workflowOperator.transformation_id === newOperator.transformation_id
    );
    if (sameOperator.length > 0) {
      newOperator.name = `${newOperator.name} (${sameOperator.length + 1})`;
    }
    return newOperator;
  }

  private _updateOperatorPosition(element: HTMLElement, operator: Operator) {
    const newPosX = Number(element.getAttribute('x'));
    const newPosY = Number(element.getAttribute('y'));
    if (operator.position.x !== newPosX || operator.position.y !== newPosY) {
      operator.position.x = newPosX;
      operator.position.y = newPosY;
      this.hasChanges = true;
    }
  }
}
