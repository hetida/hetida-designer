import { Injectable } from '@angular/core';
import { FormControl } from '@angular/forms';
import { MatDialog } from '@angular/material/dialog';
import {
  ConfirmClickEvent,
  ExecutionDialogData,
  Wiring,
  WiringDialogComponent
} from 'hd-wiring';
import { combineLatest, iif, Observable, of } from 'rxjs';
import { finalize, first, switchMap, tap } from 'rxjs/operators';
import {
  ComponentIODialogComponent,
  ComponentIoDialogData
} from 'src/app/components/component-io-dialog/component-io-dialog.component';
import {
  ConfirmDialogComponent,
  ConfirmDialogData
} from 'src/app/components/confirmation-dialog/confirm-dialog.component';
import { CopyBaseItemDialogComponent } from 'src/app/components/copy-base-item-dialog/copy-base-item-dialog.component';
import {
  WorkflowIODialogComponent,
  WorkflowIODialogData
} from 'src/app/components/workflow-io-dialog/workflow-io-dialog.component';
import { BaseItemType } from 'src/app/enums/base-item-type';
import { RevisionState } from 'src/app/enums/revision-state';
import { AbstractBaseItem, BaseItem } from 'src/app/model/base-item';
import { ComponentBaseItem } from 'src/app/model/component-base-item';
import { WorkflowBaseItem } from 'src/app/model/workflow-base-item';
import { WorkflowLink } from 'src/app/model/workflow-link';
import { Utils } from 'src/app/utils/utils';
import { PythonIdentifierValidator } from 'src/app/validation/python-identifier-validator';
import { PythonKeywordBlacklistValidator } from 'src/app/validation/python-keyword-validator';
import * as uuid from 'uuid';
import { BaseItemDialogData } from '../../model/base-item-dialog-data';
import { IOItem } from '../../model/io-item';
import { ComponentEditorService } from '../component-editor.service';
import { WiringHttpService } from '../http-service/wiring-http.service';
import { NotificationService } from '../notifications/notification.service';
import { TabItemService } from '../tab-item/tab-item.service';
import { WorkflowEditorService } from '../workflow-editor/workflow-editor.service';
import { BaseItemService } from './base-item.service';
import {
  ComponentTransformation,
  isComponentTransformation,
  isWorkflowTransformation,
  Transformation,
  WorkflowTransformation
} from '../../model/new-api/transformation';

/**
 * Actions like opening copy dialog, or other actions are collected here
 */
@Injectable({
  providedIn: 'root'
})
export class BaseItemActionService {
  constructor(
    private readonly dialog: MatDialog,
    private readonly baseItemService: BaseItemService,
    private readonly workflowService: WorkflowEditorService,
    private readonly tabItemService: TabItemService,
    private readonly notificationService: NotificationService,
    private readonly componentService: ComponentEditorService,
    private readonly wiringService: WiringHttpService
  ) {}

  public async execute(abstractBaseItem: AbstractBaseItem) {
    // TODO
    // @ts-ignore
    if (this.isIncomplete(abstractBaseItem as Transformation)) {
      return;
    }
    let title: string;
    if (abstractBaseItem.type === BaseItemType.COMPONENT) {
      title = 'Execute Component';
    } else if (abstractBaseItem.type === BaseItemType.WORKFLOW) {
      title = 'Execute Workflow';
    } else {
      console.warn(
        'A new component type is introduced or the type property of item does not have the correct spelling'
      );
      title = 'Execute Unknown';
    }

    const adapterList = await this.wiringService.getAdapterList().toPromise();

    const dialogRef = this.dialog.open<
      WiringDialogComponent,
      ExecutionDialogData,
      never
    >(WiringDialogComponent, {
      data: {
        title,
        wiringItem: abstractBaseItem,
        adapterList
      }
    });
    const componentExecution$ = (
      executeTestClickEvent: ConfirmClickEvent
    ): Observable<ComponentBaseItem> => {
      return this.componentService
        .bindWiringToComponent(
          executeTestClickEvent.id,
          executeTestClickEvent.wiring
        )
        .pipe(
          switchMap(() =>
            this.componentService.testComponent(
              executeTestClickEvent.id,
              executeTestClickEvent.wiring
            )
          )
        );
    };

    const workflowExecution$ = (
      executeTestClickEvent: ConfirmClickEvent
    ): Observable<WorkflowBaseItem> => {
      return this.workflowService
        .bindWiringToWorkflow(
          executeTestClickEvent.id,
          executeTestClickEvent.wiring
        )
        .pipe(
          switchMap(() =>
            this.workflowService.testWorkflow(
              executeTestClickEvent.id,
              executeTestClickEvent.wiring
            )
          )
        );
    };

    dialogRef.componentInstance.cancelDialogClick.subscribe(() => {
      dialogRef.close();
    });

    dialogRef.componentInstance.confirmClick
      .pipe(
        tap(() => dialogRef.close()),
        switchMap(executeTestClickEvent => {
          let saveOrUpdate$: Observable<Wiring>;
          if (Utils.isDefined(executeTestClickEvent.wiring.id)) {
            saveOrUpdate$ = this.wiringService.updateWiring(
              executeTestClickEvent.wiring
            );
          } else {
            saveOrUpdate$ = this.wiringService.saveWiring(
              executeTestClickEvent.wiring
            );
          }
          return combineLatest([of(executeTestClickEvent.id), saveOrUpdate$]);
        }),
        switchMap(([wiringItemId, savedWiring]) =>
          iif(
            () => abstractBaseItem.type === BaseItemType.WORKFLOW,
            workflowExecution$({ id: wiringItemId, wiring: savedWiring }),
            componentExecution$({ id: wiringItemId, wiring: savedWiring })
          )
        ),
        finalize(() => dialogRef.close())
      )
      .subscribe();
  }

  public editDetails(transformation: Transformation): void {
    const isReleased = this.isReleased(transformation);
    const dialogRef = this.dialog.open<
      CopyBaseItemDialogComponent,
      BaseItemDialogData,
      Transformation | undefined
    >(CopyBaseItemDialogComponent, {
      width: '640px',
      data: {
        title: `Edit ${transformation.type.toLowerCase()} ${
          transformation.name
        } ${transformation.version_tag}`,
        content: '',
        actionOk: 'Save Details',
        actionCancel: 'Cancel',
        deleteButtonText: 'Delete Draft',
        showDeleteButton: transformation.state === RevisionState.DRAFT,
        // TODO
        // @ts-ignore
        abstractBaseItem: { ...(transformation as AbstractBaseItem) },
        transformation,
        disabledState: {
          name: isReleased,
          category: isReleased,
          tag: isReleased,
          description: isReleased
        }
      }
    });

    dialogRef.componentInstance.onDelete.subscribe(
      (transformationToDelete: Transformation) =>
        this.delete(transformationToDelete).subscribe(isDeleted => {
          if (isDeleted) {
            dialogRef.close();
          }
        })
    );

    dialogRef
      .afterClosed()
      .subscribe((transformationToUpdate: Transformation | undefined) => {
        if (transformationToUpdate) {
          this.baseItemService.updateTransformation(transformationToUpdate);
        }
      });
  }

  // TODO unit test
  // group id has to be the same
  public async newRevision(transformation: Transformation) {
    if (!this.isReleased(transformation)) {
      return;
    }
    const newId = uuid().toString();
    const groupId = transformation.revision_group_id;
    let copyOfBaseItem: Transformation;
    if (transformation.type === BaseItemType.WORKFLOW) {
      // @ts-ignore
      copyOfBaseItem = (await this.copyWorkflow(
        newId,
        groupId,
        'Draft',
        // @ts-ignore
        transformation as BaseItem
      )) as Transformation;
    } else {
      // @ts-ignore
      copyOfBaseItem = this.copyComponent(
        newId,
        groupId,
        'Draft',
        // @ts-ignore
        transformation as Transformation
      ) as BaseItem;
    }
    const dialogRef = this.dialog.open<
      CopyBaseItemDialogComponent,
      BaseItemDialogData,
      Transformation | undefined
    >(CopyBaseItemDialogComponent, {
      width: '640px',
      data: {
        title: 'Create new revision?',
        content: `This ${copyOfBaseItem.type.toLowerCase()} is already released. Do you want to create a new revision?`,
        actionOk: 'Create new revision',
        actionCancel: 'Cancel',
        // @ts-ignore
        abstractBaseItem: copyOfBaseItem as BaseItem,
        transformation: copyOfBaseItem,
        disabledState: {
          name: true,
          category: false,
          tag: false,
          description: false
        }
      }
    });

    dialogRef.afterClosed().subscribe(newTransformationRevision => {
      this.saveAndNavigate(newTransformationRevision);
    });
  }

  public delete(transformation: Transformation): Observable<boolean> {
    if (this.isReleased(transformation)) {
      return of(false);
    }

    const dialogRef = this.dialog.open<
      ConfirmDialogComponent,
      ConfirmDialogData,
      boolean
    >(ConfirmDialogComponent, {
      width: '640px',
      data: {
        title: `Delete ${transformation.type.toLowerCase()} ${
          transformation.name
        } (${transformation.version_tag})`,
        content: `Do you want to delete this ${transformation.type.toLowerCase()} permanently?`,
        actionOk: `Delete ${transformation.type.toLowerCase()}`,
        actionCancel: 'Cancel'
      }
    });

    return dialogRef.afterClosed().pipe(
      switchMap(isConfirmed => {
        if (isConfirmed) {
          return this.doDeleteTransformation(transformation).pipe(
            switchMap(() => of(isConfirmed))
          );
        }
        return of(isConfirmed);
      })
    );
  }

  public isReleased(transformation: AbstractBaseItem | Transformation) {
    return transformation.state === RevisionState.RELEASED;
  }

  public publish(transformation: Transformation): void {
    if (this.isIncomplete(transformation)) {
      this.notificationService.warn(
        `This ${transformation.type.toLowerCase()} is incomplete and cannot be published`
      );
      return;
    }

    if (transformation.state === RevisionState.DRAFT) {
      const dialogRef = this.dialog.open<
        ConfirmDialogComponent,
        ConfirmDialogData,
        boolean
      >(ConfirmDialogComponent, {
        width: '640px',
        data: {
          title: `Publish component ${transformation.name} (${transformation.version_tag})`,
          content: `Do you want to publish this ${transformation.type.toLowerCase()}?`,
          actionOk: `Publish ${transformation.type.toLowerCase()}`,
          actionCancel: 'Cancel'
        }
      });

      dialogRef.afterClosed().subscribe(isConfirmed => {
        if (isConfirmed) {
          this.baseItemService.releaseTransformation(transformation);
        }
      });
    }
  }

  // TODO unit test
  // has to have a new group id
  public async copy(transformation: Transformation) {
    const newId = uuid().toString();
    const groupId = uuid().toString();
    let copyOfBaseItem: Transformation;
    if (transformation.type === BaseItemType.WORKFLOW) {
      // @ts-ignore
      copyOfBaseItem = (await this.copyWorkflow(
        newId,
        groupId,
        'Copy',
        // TODO
        // @ts-ignore
        transformation as Transformation
      )) as Transformation;
    } else {
      copyOfBaseItem = this.copyComponent(
        newId,
        groupId,
        'Copy',
        transformation
      );
    }

    let type = copyOfBaseItem.type.toLowerCase();
    type = `${type.charAt(0).toUpperCase() + type.slice(1)}`;

    // @ts-ignore
    const dialogRef = this.dialog.open<
      CopyBaseItemDialogComponent,
      Omit<BaseItemDialogData, 'content'>,
      Transformation | undefined
    >(CopyBaseItemDialogComponent, {
      width: '640px',
      data: {
        title: `Copy ${type} ${copyOfBaseItem.name} ${copyOfBaseItem.version_tag}`,
        actionOk: `Copy ${type}`,
        actionCancel: 'Cancel',
        abstractBaseItem: copyOfBaseItem as Transformation,
        transformation: copyOfBaseItem,
        disabledState: {
          name: false,
          category: false,
          tag: false,
          description: false
        }
      }
    });

    dialogRef.afterClosed().subscribe(copiedTransformation => {
      this.saveAndNavigate(copiedTransformation);
    });
  }

  public configureIO(transformation: Transformation) {
    // TODO refactor
    if (
      isWorkflowTransformation(transformation) &&
      transformation.io_interface.inputs.length === 0 &&
      transformation.io_interface.outputs.length === 0
    ) {
      return;
    }

    if (isComponentTransformation(transformation)) {
      this.configureComponentIO(transformation);
    } else {
      // @ts-ignore
      this.configureWorkflowIO(transformation as AbstractBaseItem);
    }
  }

  public showDocumentation(transformationId: string, openTabInEditMode = true) {
    this.tabItemService.addDocumentationTab(
      transformationId,
      openTabInEditMode
    );
  }

  public newWorkflow(): void {
    const dialogRef = this.dialog.open<
      CopyBaseItemDialogComponent,
      Omit<BaseItemDialogData, 'content'>,
      BaseItem | undefined
    >(CopyBaseItemDialogComponent, {
      width: '640px',
      data: {
        title: 'Create new workflow',
        actionOk: 'Create Workflow',
        actionCancel: 'Cancel',
        abstractBaseItem: this.baseItemService.createWorkflow(),
        disabledState: {
          name: false,
          category: false,
          tag: false,
          description: false
        }
      }
    });

    dialogRef.afterClosed().subscribe(baseItem => {
      if (baseItem === undefined) {
        return;
      }
      this.tabItemService.createTransformationAndOpenInNewTab(
        // TODO
        // @ts-ignore
        baseItem as Transformation
      );
    });
  }

  public newComponent(): void {
    const dialogRef = this.dialog.open<
      CopyBaseItemDialogComponent,
      Omit<BaseItemDialogData, 'content'>,
      Transformation | undefined
    >(CopyBaseItemDialogComponent, {
      width: '640px',
      data: {
        title: 'Create new component',
        actionOk: 'Create Component',
        actionCancel: 'Cancel',
        // TODO
        // @ts-ignore
        abstractBaseItem: this.baseItemService.getDefaultComponentTransformation() as AbstractBaseItem,
        transformation: this.baseItemService.getDefaultComponentTransformation(),
        disabledState: {
          name: false,
          category: false,
          tag: false,
          description: false
        }
      }
    });

    dialogRef.afterClosed().subscribe(transformation => {
      if (transformation) {
        this.tabItemService.createTransformationAndOpenInNewTab(transformation);
      }
    });
  }

  public deprecate(transformation: Transformation) {
    if (transformation.state !== RevisionState.RELEASED) {
      return;
    }
    const dialogRef = this.dialog.open<
      ConfirmDialogComponent,
      ConfirmDialogData,
      boolean
    >(ConfirmDialogComponent, {
      width: '640px',
      data: {
        title: `Deprecate ${transformation.type.toLowerCase()} ${
          transformation.name
        } (${transformation.version_tag})`,
        content: `Do you want to deprecate this ${transformation.type.toLowerCase()}?`,
        actionOk: `Deprecate ${transformation.type.toLowerCase()}`,
        actionCancel: 'Cancel'
      }
    });

    dialogRef.afterClosed().subscribe(isConfirmed => {
      if (isConfirmed) {
        this.baseItemService.disableTransformation(transformation);
      }
    });
  }

  public isIncomplete(transformation: Transformation | undefined): boolean {
    let isIncomplete = true;
    if (isWorkflowTransformation(transformation)) {
      isIncomplete = this.isWorkflowIncomplete(transformation);
    } else if (isComponentTransformation(transformation)) {
      // TODO extract and test method
      isIncomplete =
        transformation.io_interface.inputs.length === 0 &&
        transformation.io_interface.outputs.length === 0;
    }
    return isIncomplete;
  }

  public doDeleteTransformation(
    transformation: Transformation
  ): Observable<void> {
    this.tabItemService.deselectActiveTabItem();
    return this.baseItemService.deleteTransformation(transformation.id);
  }

  // TODO unit test
  private async copyWorkflow(
    newId: string,
    groupId: string,
    suffix: string,
    abstractBaseItem: AbstractBaseItem
  ): Promise<WorkflowBaseItem> {
    const workflow = await this.workflowService
      .getWorkflow(abstractBaseItem.id)
      .pipe(first(workflowBaseItem => workflowBaseItem !== undefined))
      .toPromise();

    const wirings: Wiring[] = [];
    const links: WorkflowLink[] = [];
    // give new ids to everything
    const copy = {
      ...workflow,
      id: newId,
      groupId,
      state: RevisionState.DRAFT,
      tag: `${workflow.tag} ${suffix}`,
      inputs: workflow.inputs.map(input => ({
        ...input,
        id: uuid().toString(),
        oldId: input.id,
        operator: undefined
      })),
      outputs: workflow.outputs.map(output => ({
        ...output,
        id: uuid().toString(),
        oldId: output.id,
        operator: undefined
      })),
      operators: workflow.operators.map(operator => ({
        ...operator,
        id: uuid().toString(),
        oldId: operator.id
      })),
      links,
      wirings
    };

    // Re-assign the links.
    for (const link of workflow.links) {
      let newFromOperatorId: string;
      let newToOperatorId: string;
      let newFromConnectorId: string;
      let newToConnectorId: string;
      if (link.fromOperator === workflow.id) {
        newFromOperatorId = newId;
        const fromConnector = copy.inputs.find(
          input => input.oldId === link.fromConnector
        );
        if (fromConnector === undefined) {
          throw new Error(`no workflow input with id ${link.fromConnector}`);
        }
        newFromConnectorId = fromConnector.id;
      } else {
        const fromOperator = copy.operators.find(
          operator => operator.oldId === link.fromOperator
        );
        if (fromOperator === undefined) {
          throw new Error(`no operator with id ${link.fromOperator}`);
        }
        newFromOperatorId = fromOperator.id;
        const fromConnector = fromOperator.outputs.find(
          output => output.id === link.fromConnector
        );
        if (fromConnector === undefined) {
          throw new Error(`no workflow output with id ${link.fromConnector}`);
        }
        newFromConnectorId = fromConnector.id;
      }

      if (link.toOperator === workflow.id) {
        newToOperatorId = newId;
        const toConnector = copy.outputs.find(
          output => output.oldId === link.toConnector
        );
        if (toConnector === undefined) {
          throw new Error(`no workflow output with id ${link.toConnector}`);
        }
        newToConnectorId = toConnector.id;
      } else {
        const toOperator = copy.operators.find(
          operator => operator.oldId === link.toOperator
        );
        if (toOperator === undefined) {
          throw new Error(`no input with id ${link.toOperator}`);
        }
        newToOperatorId = toOperator.id;
        const toConnector = toOperator.inputs.find(
          input => input.id === link.toConnector
        );
        if (toConnector === undefined) {
          throw new Error(`no workflow input with id ${link.toConnector}`);
        }
        newToConnectorId = toConnector.id;
      }

      // Create the link between workflow and operators.
      const newLink = {
        id: uuid().toString(),
        fromOperator: newFromOperatorId,
        fromConnector: newFromConnectorId,
        toOperator: newToOperatorId,
        toConnector: newToConnectorId,
        path: [...link.path]
      };

      // Set link target on the workflow io.
      const workflowInputFrom = copy.inputs.find(
        input => input.id === newFromConnectorId
      );
      if (workflowInputFrom !== undefined) {
        workflowInputFrom.connector = newToConnectorId;
        workflowInputFrom.operator = newToOperatorId;
      }
      const workflowOutputTo = copy.outputs.find(
        output => output.id === newToConnectorId
      );
      if (workflowOutputTo !== undefined) {
        workflowOutputTo.connector = newFromConnectorId;
        workflowOutputTo.operator = newFromOperatorId;
      }
      copy.links.push(newLink);
    }

    // Copy constants (no link).
    for (const input of workflow.inputs) {
      if (input.constant === false) {
        continue;
      }
      const operator = copy.operators.find(
        operatorCandidate => operatorCandidate.oldId === input.operator
      );
      if (operator === undefined) {
        throw new Error(`No operator for id ${input.operator}`);
      }
      const opInput = operator.inputs.find(
        operatorInput => operatorInput.id === input.connector
      );
      if (opInput === undefined) {
        throw new Error(`No input for id ${input.connector}`);
      }
      const copyInput = copy.inputs.find(
        copyWorkflowInput => copyWorkflowInput.oldId === input.id
      );
      if (copyInput === undefined) {
        throw new Error(`No workflow input for id ${input.id}`);
      }
      copyInput.connector = opInput.id;
      copyInput.operator = operator.id;
    }

    // Remove all io we don't know the connections for.
    copy.inputs = copy.inputs.filter(
      input => input.connector !== undefined && input.operator !== undefined
    );
    copy.outputs = copy.outputs.filter(
      output => output.connector !== undefined && output.operator !== undefined
    );

    return copy;
  }

  // TODO unit test
  // state has to be draft
  private copyComponent(
    newId: string,
    groupId: string,
    suffix: string,
    componentTransformation: ComponentTransformation
  ): Transformation {
    return {
      ...componentTransformation,
      id: newId,
      revision_group_id: groupId,
      state: RevisionState.DRAFT,
      version_tag: `${componentTransformation.version_tag} ${suffix}`,
      io_interface: {
        inputs: componentTransformation.io_interface.inputs.map(input => ({
          ...input,
          id: uuid().toString()
        })),
        outputs: componentTransformation.io_interface.outputs.map(output => ({
          ...output,
          id: uuid().toString()
        }))
      },
      test_wiring: {
        input_wirings: [],
        output_wirings: []
      }
    };
  }

  private saveAndNavigate(transformation: Transformation | undefined): void {
    if (transformation === undefined) {
      return;
    }
    this.tabItemService.createTransformationAndOpenInNewTab(transformation);
  }

  // TODO refactor / unit test
  /**
   * checks if the workflow is in an incomplete state
   * - has no operators
   * - any input name is empty or not a valid python identifier
   * - any output name is empty or not a valid python identifier
   * - any input name is a python keyword
   * - any output name is a python keyword
   * - there isn't a link to every output
   * - there isn't a link from every input
   */
  private isWorkflowIncomplete(workflow: WorkflowTransformation): boolean {
    const workflowContent = workflow.content;
    // TODO rename
    // @ts-ignore
    const checkName = (name: string, id: string) => {
      const formControl = new FormControl(name, [
        PythonIdentifierValidator(false),
        PythonKeywordBlacklistValidator()
      ]);
      if (formControl.invalid) {
        return false;
      }
      return workflowContent.links.some(
        link => link.start.connector.id === id || link.end.connector.id === id
      );
    };
    return (
      workflowContent.operators.length === 0
      // TODO transformation.io_interface.inputs or transformation.content.inputs
      // || workflow.inputs.some(
      //   input =>
      //     input.constant === false && checkName(input.name, input.id) === false
      // ) ||
      // workflow.outputs.some(
      //   output =>
      //     output.constant === false &&
      //     checkName(output.name, output.id) === false
      // )
    );
  }

  private configureComponentIO(
    componentTransformation: ComponentTransformation
  ) {
    const componentIoDialogData: ComponentIoDialogData = {
      // TODO: Check whether the item is being mutated and if so remove the mutations. Then remove JSON.*().
      componentTransformation: JSON.parse(
        JSON.stringify(componentTransformation)
      ),
      editMode: componentTransformation.state !== RevisionState.RELEASED,
      actionOk: 'Save',
      actionCancel: 'Cancel'
    };

    const dialogRef = this.dialog.open<
      ComponentIODialogComponent,
      ComponentIoDialogData,
      ComponentTransformation | undefined
    >(ComponentIODialogComponent, {
      minHeight: '200px',
      data: componentIoDialogData
    });

    dialogRef.afterClosed().subscribe(updatedComponentTransformation => {
      if (updatedComponentTransformation) {
        this.baseItemService.updateTransformation(
          updatedComponentTransformation
        );
      }
    });
  }

  private configureWorkflowIO(abstractBaseItem: AbstractBaseItem) {
    this.workflowService
      .getWorkflow(abstractBaseItem.id)
      .pipe(first())
      .subscribe(workflowBaseItem => {
        if (workflowBaseItem === undefined) {
          return;
        }

        const dialogRef = this.dialog.open<
          WorkflowIODialogComponent,
          WorkflowIODialogData,
          false | { inputs: IOItem[]; outputs: IOItem[] }
        >(WorkflowIODialogComponent, {
          width: '95%',
          minHeight: '200px',
          data: {
            // TODO refactor all mutations in workflow dialog component and remove stringify .
            workflow: JSON.parse(JSON.stringify(workflowBaseItem)),
            editMode: workflowBaseItem.state !== RevisionState.RELEASED,
            actionOk: 'Save',
            actionCancel: 'Cancel'
          }
        });

        dialogRef
          .afterClosed()
          .pipe(first())
          .subscribe(result => {
            if (result) {
              const ioItemIds = [...result.inputs, ...result.outputs].map(
                ioItem => `${ioItem.operator}_${ioItem.connector}`
              );

              const innerLinks = workflowBaseItem.links.filter(link => {
                const fromIoItemId = `${link.fromOperator}_${link.fromConnector}`;
                const toIoItemId = `${link.toOperator}_${link.toConnector}`;
                const isOuterLink =
                  ioItemIds.includes(fromIoItemId) ||
                  ioItemIds.includes(toIoItemId);
                return !isOuterLink;
              });

              const inputIoItems = this._updateIoItemPositions(
                result.inputs,
                true,
                workflowBaseItem
              );
              const outputIoItems = this._updateIoItemPositions(
                result.outputs,
                false,
                workflowBaseItem
              );
              const links = [
                ...innerLinks,
                ...this._createLinks(
                  inputIoItems,
                  outputIoItems,
                  workflowBaseItem
                )
              ];

              const updatedWorkflow = {
                ...workflowBaseItem,
                inputs: inputIoItems,
                outputs: outputIoItems,
                links
              };

              this.workflowService.updateWorkflow(updatedWorkflow);
            }
          });
      });
  }

  private _updateIoItemPositions(
    ioItems: IOItem[],
    isInput: boolean,
    workflowBaseItem: WorkflowBaseItem
  ): IOItem[] {
    return ioItems.map(ioItem =>
      this._updateIoItemPosition(ioItem, isInput, workflowBaseItem)
    );
  }

  private _updateIoItemPosition(
    ioItem: IOItem,
    isInput: boolean,
    workflowBaseItem: WorkflowBaseItem
  ): IOItem {
    const operator = workflowBaseItem.operators.find(
      op => op.id === ioItem.operator
    );
    if (operator === undefined) {
      throw new Error('Operator not found!');
    }
    let connectorIndex = operator.inputs.findIndex(
      cio => cio.id === ioItem.connector
    );
    if (connectorIndex === -1) {
      connectorIndex = operator.outputs.findIndex(
        cio => cio.id === ioItem.connector
      );
      if (connectorIndex === -1) {
        throw new Error('Connector not found!');
      }
    }

    return {
      ...ioItem,
      posX: operator.posX + (isInput ? -250 : 450),
      posY: operator.posY + 60 + connectorIndex * 30
    };
  }

  private _createLinks(
    inputItems: IOItem[],
    outputItems: IOItem[],
    workflowBaseItem: WorkflowBaseItem
  ): WorkflowLink[] {
    const isConnectedIoItem = (ioItem: IOItem) =>
      !Utils.string.isEmptyOrUndefined(ioItem.name) || ioItem.constant === true;

    const inputLinks = inputItems
      .filter(isConnectedIoItem)
      .map(ioItem => this._createInputLink(ioItem, workflowBaseItem));

    const outputLinks = outputItems
      .filter(isConnectedIoItem)
      .map(ioItem => this._createOutputLink(ioItem, workflowBaseItem));

    return [...inputLinks, ...outputLinks];
  }

  private _createInputLink(
    io: IOItem,
    workflowBaseItem: WorkflowBaseItem
  ): WorkflowLink {
    return {
      id: uuid().toString(),
      fromOperator: workflowBaseItem.id,
      fromConnector: io.id,
      toOperator: io.operator,
      toConnector: io.connector,
      path: []
    };
  }

  private _createOutputLink(
    io: IOItem,
    workflowBaseItem: WorkflowBaseItem
  ): WorkflowLink {
    return {
      id: uuid().toString(),
      toOperator: workflowBaseItem.id,
      toConnector: io.id,
      fromOperator: io.operator,
      fromConnector: io.connector,
      path: []
    };
  }
}
