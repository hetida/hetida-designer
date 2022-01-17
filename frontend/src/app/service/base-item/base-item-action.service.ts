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
import {
  isComponentBaseItem,
  isWorkflowBaseItem
} from 'src/app/store/base-item/base-item-guards';
import { Utils } from 'src/app/utils/utils';
import { PythonIdentifierValidator } from 'src/app/validation/PythonIdentifierValidator';
import { PythonKeywordBlacklistValidator } from 'src/app/validation/PythonKeywordValidator';
import * as uuid from 'uuid';
import { BaseItemDialogData } from '../../model/BaseItemDialogData';
import { IOItem } from '../../model/io-item';
import { ComponentEditorService } from '../component-editor.service';
import { WiringHttpService } from '../http-service/wiring-http.service';
import { NotificationService } from '../notifications/notification.service';
import { TabItemService } from '../tab-item/tab-item.service';
import { WorkflowEditorService } from '../workflow-editor.service';
import { BaseItemService } from './base-item.service';

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
    if (await this.isIncomplete(abstractBaseItem)) {
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

  public editDetails(baseItem: BaseItem): void {
    const isReleased = this.isReleased(baseItem);
    const dialogRef = this.dialog.open<
      CopyBaseItemDialogComponent,
      BaseItemDialogData,
      BaseItem | undefined
    >(CopyBaseItemDialogComponent, {
      width: '640px',
      data: {
        title: `Edit ${baseItem.type.toLowerCase()} ${baseItem.name} ${
          baseItem.tag
        }`,
        content: '',
        actionOk: 'Save Details',
        actionCancel: 'Cancel',
        deleteButtonText: 'Delete Draft',
        showDeleteButton: baseItem.state === RevisionState.DRAFT,
        abstractBaseItem: { ...baseItem },
        disabledState: {
          name: isReleased,
          category: isReleased,
          tag: isReleased,
          description: isReleased
        }
      }
    });

    // TODO call confirmation mail
    dialogRef.componentInstance.onDelete.subscribe(
      (toBeDeleteBaseItem: BaseItem) =>
        this.delete(toBeDeleteBaseItem).subscribe(isDeleted => {
          if (isDeleted) {
            dialogRef.close();
          }
        })
    );

    dialogRef
      .afterClosed()
      .subscribe((selectedAbstractBaseItem: AbstractBaseItem | undefined) => {
        if (selectedAbstractBaseItem) {
          if (isWorkflowBaseItem(selectedAbstractBaseItem)) {
            this.workflowService.updateWorkflow(selectedAbstractBaseItem);
          } else if (isComponentBaseItem(selectedAbstractBaseItem)) {
            this.componentService.updateComponent(selectedAbstractBaseItem);
          } else {
            throw Error('workflow or component base item expected');
          }
        }
      });
  }

  public async newRevision(baseItem: BaseItem) {
    if (!this.isReleased(baseItem)) {
      return;
    }
    const newId = uuid().toString();
    const groupId = baseItem.groupId;
    let copyOfBaseItem: BaseItem;
    if (baseItem.type === BaseItemType.WORKFLOW) {
      copyOfBaseItem = await this.copyWorkflow(
        newId,
        groupId,
        'Draft',
        baseItem
      );
    } else {
      copyOfBaseItem = await this.copyComponent(
        newId,
        groupId,
        'Draft',
        baseItem
      );
    }
    const dialogRef = this.dialog.open<
      CopyBaseItemDialogComponent,
      BaseItemDialogData,
      BaseItem | undefined
    >(CopyBaseItemDialogComponent, {
      width: '640px',
      data: {
        title: 'Create new revision?',
        content: `This ${copyOfBaseItem.type.toLowerCase()} is already released. Do you want to create a new revision?`,
        actionOk: 'Create new revision',
        actionCancel: 'Cancel',
        abstractBaseItem: copyOfBaseItem,
        disabledState: {
          name: true,
          category: false,
          tag: false,
          description: false
        }
      }
    });

    dialogRef.afterClosed().subscribe(newBaseItemRevision => {
      this.saveAndNavigate(newBaseItemRevision);
    });
  }

  public delete(abstractBaseItem: AbstractBaseItem): Observable<boolean> {
    if (this.isReleased(abstractBaseItem)) {
      return of(false);
    }

    const dialogRef = this.dialog.open<
      ConfirmDialogComponent,
      ConfirmDialogData,
      boolean
    >(ConfirmDialogComponent, {
      width: '640px',
      data: {
        title: `Delete ${abstractBaseItem.type.toLowerCase()} ${
          abstractBaseItem.name
        } (${abstractBaseItem.tag})`,
        content: `Do you want to delete this ${abstractBaseItem.type.toLowerCase()} permanently?`,
        actionOk: `Delete ${abstractBaseItem.type.toLowerCase()}`,
        actionCancel: 'Cancel'
      }
    });

    return dialogRef.afterClosed().pipe(
      switchMap(isConformed => {
        if (isConformed) {
          return this.deleteAction(abstractBaseItem).pipe(
            switchMap(() => of(isConformed))
          );
        }
        return of(isConformed);
      })
    );
  }

  public isReleased(abstractBaseItem: AbstractBaseItem) {
    return abstractBaseItem.state === RevisionState.RELEASED;
  }

  public async publish(baseItem: BaseItem): Promise<void> {
    if (await this.isIncomplete(baseItem)) {
      this.notificationService.warn(
        `This ${baseItem.type.toLowerCase()} is incomplete and cannot be published`
      );
      return;
    }

    if (baseItem.state === RevisionState.DRAFT) {
      const dialogRef = this.dialog.open<
        ConfirmDialogComponent,
        ConfirmDialogData,
        boolean
      >(ConfirmDialogComponent, {
        width: '640px',
        data: {
          title: `Publish component ${baseItem.name} (${baseItem.tag})`,
          content: `Do you want to publish this ${baseItem.type.toLowerCase()}?`,
          actionOk: `Publish ${baseItem.type.toLowerCase()}`,
          actionCancel: 'Cancel'
        }
      });

      dialogRef.afterClosed().subscribe(isConfirmed => {
        if (isConfirmed) {
          this.baseItemService.releaseBaseItem(baseItem);
        }
      });
    }
  }

  public async copy(abstractBaseItem: AbstractBaseItem) {
    const newId = uuid().toString();
    const groupId = uuid().toString();
    let copyOfBaseItem: BaseItem;
    if (abstractBaseItem.type === BaseItemType.WORKFLOW) {
      copyOfBaseItem = await this.copyWorkflow(
        newId,
        groupId,
        'Copy',
        abstractBaseItem
      );
    } else {
      copyOfBaseItem = await this.copyComponent(
        newId,
        groupId,
        'Copy',
        abstractBaseItem
      );
    }

    let type = copyOfBaseItem.type.toLowerCase();
    type = `${type.charAt(0).toUpperCase() + type.slice(1)}`;

    const dialogRef = this.dialog.open<
      CopyBaseItemDialogComponent,
      Omit<BaseItemDialogData, 'content'>,
      BaseItem | undefined
    >(CopyBaseItemDialogComponent, {
      width: '640px',
      data: {
        title: `Copy ${type} ${copyOfBaseItem.name} ${copyOfBaseItem.tag}`,
        actionOk: `Copy ${type}`,
        actionCancel: 'Cancel',
        abstractBaseItem: copyOfBaseItem,
        disabledState: {
          name: false,
          category: false,
          tag: false,
          description: false
        }
      }
    });

    dialogRef.afterClosed().subscribe(baseItem => {
      this.saveAndNavigate(baseItem);
    });
  }

  public configureIO(abstractBaseItem: AbstractBaseItem) {
    if (
      abstractBaseItem.inputs.length === 0 &&
      abstractBaseItem.outputs.length === 0 &&
      abstractBaseItem.type === BaseItemType.WORKFLOW
    ) {
      return;
    }

    if (abstractBaseItem.type === BaseItemType.COMPONENT) {
      this.configureComponentIO(abstractBaseItem);
    } else {
      this.configureWorkflowIO(abstractBaseItem);
    }
  }

  public showDocumentation(
    abstractBaseItem: AbstractBaseItem,
    openTabInEditMode = true
  ) {
    this.tabItemService.addDocumentationTab(
      abstractBaseItem.id,
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
      this.tabItemService.createBaseItemAndOpenInNewTab(baseItem);
    });
  }

  public newComponent(): void {
    const dialogRef = this.dialog.open<
      CopyBaseItemDialogComponent,
      Omit<BaseItemDialogData, 'content'>,
      BaseItem | undefined
    >(CopyBaseItemDialogComponent, {
      width: '640px',
      data: {
        title: 'Create new component',
        actionOk: 'Create Component',
        actionCancel: 'Cancel',
        abstractBaseItem: this.baseItemService.createComponent(),
        disabledState: {
          name: false,
          category: false,
          tag: false,
          description: false
        }
      }
    });

    dialogRef.afterClosed().subscribe(baseItem => {
      if (baseItem) {
        this.tabItemService.createBaseItemAndOpenInNewTab(baseItem);
      }
    });
  }

  public deprecate(abstractBaseItem: AbstractBaseItem) {
    if (abstractBaseItem.state !== RevisionState.RELEASED) {
      return;
    }
    const dialogRef = this.dialog.open<
      ConfirmDialogComponent,
      ConfirmDialogData,
      boolean
    >(ConfirmDialogComponent, {
      width: '640px',
      data: {
        title: `Deprecate ${abstractBaseItem.type.toLowerCase()} ${
          abstractBaseItem.name
        } (${abstractBaseItem.tag})`,
        content: `Do you want to deprecate this ${abstractBaseItem.type.toLowerCase()}?`,
        actionOk: `Deprecate ${abstractBaseItem.type.toLowerCase()}`,
        actionCancel: 'Cancel'
      }
    });

    dialogRef.afterClosed().subscribe(isConfirmed => {
      if (isConfirmed) {
        this.baseItemService.disableBaseItem(abstractBaseItem);
      }
    });
  }

  public async isIncomplete(
    abstractBaseItem: AbstractBaseItem
  ): Promise<boolean> {
    let isIncomplete = false;
    if (abstractBaseItem === undefined) {
      return true;
    }
    if (abstractBaseItem.type === BaseItemType.WORKFLOW) {
      isIncomplete = await this.isWorkflowIncomplete(abstractBaseItem);
      return isIncomplete;
    }
    isIncomplete =
      abstractBaseItem.inputs.length === 0 &&
      abstractBaseItem.outputs.length === 0;
    return isIncomplete;
  }

  public deleteAction(
    abstractBaseItem: AbstractBaseItem
  ): Observable<WorkflowBaseItem | ComponentBaseItem> {
    this.tabItemService.deselectActiveBaseItem();
    if (abstractBaseItem.type === BaseItemType.WORKFLOW) {
      return this.workflowService.deleteWorkflow(abstractBaseItem.id);
    }
    return this.componentService.deleteComponent(abstractBaseItem.id);
  }

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

  private async copyComponent(
    newId: string,
    groupId: string,
    suffix: string,
    abstractBaseItem: AbstractBaseItem
  ): Promise<ComponentBaseItem> {
    const component = await this.componentService
      .getComponent(abstractBaseItem.id)
      .pipe(first())
      .toPromise();

    return {
      ...component,
      id: newId,
      groupId,
      state: RevisionState.DRAFT,
      tag: `${component.tag} ${suffix}`,
      inputs: component.inputs.map(input => ({
        ...input,
        id: uuid().toString()
      })),
      outputs: component.outputs.map(output => ({
        ...output,
        id: uuid().toString()
      })),
      wirings: []
    };
  }

  private saveAndNavigate(baseItem: BaseItem | undefined): void {
    if (baseItem === undefined) {
      return;
    }
    // Persist...
    let persistBaseItem$: Observable<BaseItem>;
    if (baseItem.type === BaseItemType.WORKFLOW) {
      persistBaseItem$ = this.saveWorkflow(baseItem);
    } else {
      persistBaseItem$ = this.saveComponent(baseItem);
    }

    // ...and navigate.
    persistBaseItem$.subscribe(() => {
      if (baseItem.type === BaseItemType.COMPONENT) {
        // Updating component since code generation needs to run again to ensure that
        // possibly edited name, description and category are correct in the code
        this.componentService.updateComponent(baseItem);
      }
      this.tabItemService.addBaseItemTab(baseItem.id);
    });
  }

  private saveComponent(component: ComponentBaseItem) {
    // persist new component
    return this.componentService.createComponent(component);
  }

  private saveWorkflow(workflow: WorkflowBaseItem) {
    // persist new workflow
    return this.workflowService.createWorkflow(workflow);
  }

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
  private async isWorkflowIncomplete(
    baseItem: AbstractBaseItem
  ): Promise<boolean> {
    const workflow = await this.workflowService
      .getWorkflow(baseItem.id)
      .pipe(first())
      .toPromise();
    if (workflow === undefined) {
      return true;
    }
    const checkName = (name: string, id: string) => {
      const fc = new FormControl(name, [
        PythonIdentifierValidator(false),
        PythonKeywordBlacklistValidator()
      ]);
      if (fc.invalid) {
        return false;
      }
      return workflow.links.some(
        link => link.fromConnector === id || link.toConnector === id
      );
    };
    return (
      workflow.operators.length === 0 ||
      workflow.inputs.some(
        input =>
          input.constant === false && checkName(input.name, input.id) === false
      ) ||
      workflow.outputs.some(
        output =>
          output.constant === false &&
          checkName(output.name, output.id) === false
      )
    );
  }

  private configureComponentIO(abstractBaseItem: AbstractBaseItem) {
    this.componentService
      .getComponent(abstractBaseItem.id)
      .pipe(first())
      .subscribe(component => {
        if (component === undefined) {
          return;
        }

        const componentIoDialogData: ComponentIoDialogData = {
          // TODO: Check whether the item is being mutated and if so remove the mutations. Then remove JSON.*().
          componentBaseItem: JSON.parse(JSON.stringify(component)),
          editMode: component.state !== RevisionState.RELEASED,
          actionOk: 'Save',
          actionCancel: 'Cancel'
        };

        const dialogRef = this.dialog.open<
          ComponentIODialogComponent,
          ComponentIoDialogData,
          ComponentBaseItem | undefined
        >(ComponentIODialogComponent, {
          minHeight: '200px',
          data: componentIoDialogData
        });

        dialogRef.afterClosed().subscribe(componentBaseItem => {
          if (componentBaseItem) {
            this.componentService.updateComponent(componentBaseItem);
          }
        });
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
