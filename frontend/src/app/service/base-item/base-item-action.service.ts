import { Injectable } from '@angular/core';
import { FormControl } from '@angular/forms';
import { MatDialog } from '@angular/material/dialog';
import {
  ConfirmClickEvent,
  ExecutionDialogData,
  WiringDialogComponent
} from 'hd-wiring';
import { Observable, of } from 'rxjs';
import { finalize, first, map, switchMap, tap } from 'rxjs/operators';
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
import { AbstractBaseItem } from 'src/app/model/base-item';
import { PythonIdentifierValidator } from 'src/app/validation/python-identifier-validator';
import { PythonKeywordBlacklistValidator } from 'src/app/validation/python-keyword-validator';
import * as uuid from 'uuid';
import { BaseItemDialogData } from '../../model/base-item-dialog-data';
import { NotificationService } from '../notifications/notification.service';
import { TabItemService } from '../tab-item/tab-item.service';
import { BaseItemService } from './base-item.service';
import {
  ComponentTransformation,
  isComponentTransformation,
  isWorkflowTransformation,
  Transformation,
  WorkflowTransformation
} from '../../model/new-api/transformation';
import { Store } from '@ngrx/store';
import { TransformationState } from 'src/app/store/transformation/transformation.state';
import { selectTransformationById } from 'src/app/store/transformation/transformation.selectors';
import { ExecutionResponse } from '../../components/protocol-viewer/protocol-viewer.component';
import { IOConnector } from 'src/app/model/new-api/io-connector';
import { Link } from 'src/app/model/new-api/link';
import { Constant } from 'src/app/model/new-api/constant';
import { TransformationHttpService } from '../http-service/transformation-http.service';
import { Utils } from '../../utils/utils';

/**
 * Actions like opening copy dialog, or other actions are collected here
 */
@Injectable({
  providedIn: 'root'
})
export class BaseItemActionService {
  constructor(
    private readonly dialog: MatDialog,
    private readonly transformationStore: Store<TransformationState>,
    private readonly transformationHttpService: TransformationHttpService,
    private readonly baseItemService: BaseItemService,
    private readonly tabItemService: TabItemService,
    private readonly notificationService: NotificationService
  ) {}

  public async execute(transformation: Transformation) {
    if (this.isIncomplete(transformation)) {
      return;
    }

    let title: string;

    if (transformation.type === BaseItemType.COMPONENT) {
      title = 'Execute Component';
    } else if (transformation.type === BaseItemType.WORKFLOW) {
      title = 'Execute Workflow';
    } else {
      console.warn(
        'A new component type is introduced or the type property of item does not have the correct spelling'
      );
      title = 'Execute Unknown';
    }

    const adapterList = await this.transformationHttpService
      .getAdapterList()
      .toPromise();

    const dialogRef = this.dialog.open<
      WiringDialogComponent,
      ExecutionDialogData,
      never
    >(WiringDialogComponent, {
      data: {
        title,
        wiringItem: transformation,
        adapterList
      }
    });

    const transformationExecution$ = (
      executeTestClickEvent: ConfirmClickEvent
    ): Observable<ExecutionResponse> => {
      return this.baseItemService.testTransformation(
        executeTestClickEvent.id,
        executeTestClickEvent.test_wiring
      );
    };

    dialogRef.componentInstance.cancelDialogClick.subscribe(() => {
      dialogRef.close();
    });

    dialogRef.componentInstance.confirmClick
      .pipe(
        tap(() => dialogRef.close()),
        switchMap(executeTestClickEvent =>
          this.transformationStore
            .select(selectTransformationById(executeTestClickEvent.id))
            .pipe(
              first(),
              map(selectedTransformation => ({
                selectedTransformation,
                test_wiring: executeTestClickEvent.test_wiring
              }))
            )
        ),
        switchMap(({ selectedTransformation, test_wiring }) =>
          // TODO if a transformation is set to released,
          // it can't be updated by a new test_wiring and will throw a error 403 (Forbidden)
          this.baseItemService.updateTransformation({
            ...selectedTransformation,
            test_wiring
          })
        ),
        switchMap(updatedTransformation$ =>
          transformationExecution$({
            id: updatedTransformation$.id,
            test_wiring: updatedTransformation$.test_wiring
          })
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
      .pipe(
        switchMap((transformationToUpdate: Transformation | undefined) => {
          if (transformationToUpdate) {
            return this.baseItemService.updateTransformation(
              transformationToUpdate
            );
          }
          return of(null);
        })
      )
      .subscribe();
  }

  // TODO unit test
  public newRevision(transformation: Transformation): void {
    if (!this.isReleased(transformation)) {
      return;
    }
    const newId = uuid().toString();
    const groupId = transformation.revision_group_id;
    const copyOfTransformation: Transformation = this.copyTransformation(
      newId,
      groupId,
      'Draft',
      transformation
    );
    const dialogRef = this.dialog.open<
      CopyBaseItemDialogComponent,
      BaseItemDialogData,
      Transformation | undefined
    >(CopyBaseItemDialogComponent, {
      width: '640px',
      data: {
        title: 'Create new revision?',
        content: `This ${copyOfTransformation.type.toLowerCase()} is already released. Do you want to create a new revision?`,
        actionOk: 'Create new revision',
        actionCancel: 'Cancel',
        transformation: copyOfTransformation,
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

      dialogRef
        .afterClosed()
        .pipe(
          switchMap(isConfirmed => {
            if (isConfirmed) {
              return this.baseItemService.releaseTransformation(transformation);
            }
            return of(null);
          })
        )
        .subscribe();
    }
  }

  // TODO unit test
  public copy(transformation: Transformation): void {
    const newId = uuid().toString();
    const groupId = uuid().toString();
    const copyOfTransformation: Transformation = this.copyTransformation(
      newId,
      groupId,
      'Copy',
      transformation
    );

    let type = copyOfTransformation.type.toLowerCase();
    type = `${type.charAt(0).toUpperCase() + type.slice(1)}`;

    const dialogRef = this.dialog.open<
      CopyBaseItemDialogComponent,
      Omit<BaseItemDialogData, 'content'>,
      Transformation | undefined
    >(CopyBaseItemDialogComponent, {
      width: '640px',
      data: {
        title: `Copy ${type} ${copyOfTransformation.name} ${copyOfTransformation.version_tag}`,
        actionOk: `Copy ${type}`,
        actionCancel: 'Cancel',
        transformation: copyOfTransformation,
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
    if (
      isWorkflowTransformation(transformation) &&
      transformation.content.inputs.length === 0 &&
      transformation.content.outputs.length === 0 &&
      transformation.content.constants.length === 0
    ) {
      return;
    }

    if (isComponentTransformation(transformation)) {
      this.configureComponentIO(transformation);
    } else {
      this.configureWorkflowIO(transformation);
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
      Transformation | undefined
    >(CopyBaseItemDialogComponent, {
      width: '640px',
      data: {
        title: 'Create new workflow',
        actionOk: 'Create Workflow',
        actionCancel: 'Cancel',
        transformation: this.baseItemService.getDefaultWorkflowTransformation(),
        disabledState: {
          name: false,
          category: false,
          tag: false,
          description: false
        }
      }
    });

    dialogRef.afterClosed().subscribe(transformation => {
      if (transformation === undefined) {
        return;
      }
      this.tabItemService.createTransformationAndOpenInNewTab(transformation);
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

    dialogRef
      .afterClosed()
      .pipe(
        switchMap(isConfirmed => {
          if (isConfirmed) {
            return this.baseItemService.disableTransformation(transformation);
          }
          return of(null);
        })
      )
      .subscribe();
  }

  public isIncomplete(transformation: Transformation | undefined): boolean {
    let isIncomplete = true;
    if (isWorkflowTransformation(transformation)) {
      isIncomplete = this.isWorkflowIncomplete(transformation);
    } else if (isComponentTransformation(transformation)) {
      isIncomplete =
        transformation.io_interface.inputs.length === 0 &&
        transformation.io_interface.outputs.length === 0;
    }
    return isIncomplete;
  }

  public isWorkflowWithoutIo(
    workflowTransformation: WorkflowTransformation | undefined
  ): boolean {
    const isWorkflowWithoutIo =
      workflowTransformation.content.inputs.length === 0 &&
      workflowTransformation.content.outputs.length === 0 &&
      workflowTransformation.content.constants.length === 0;
    return isWorkflowWithoutIo;
  }

  public doDeleteTransformation(
    transformation: Transformation
  ): Observable<void> {
    this.tabItemService.deselectActiveTabItem();
    return this.baseItemService.deleteTransformation(transformation.id);
  }

  // TODO unit test
  private copyTransformation(
    newId: string,
    groupId: string,
    suffix: string,
    transformation: Transformation
  ): Transformation {
    const copy: Transformation = {
      ...transformation,
      id: newId,
      revision_group_id: groupId,
      version_tag: `${transformation.version_tag} ${suffix}`,
      state: RevisionState.DRAFT,
      // io_interface is generated in the backend, so we just send empty arrays
      io_interface: {
        inputs: [],
        outputs: []
      }
    };
    return copy;
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
    // TODO Need to be rebuild.
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
      workflowContent.operators.length === 0 ||
      workflowContent.inputs.some(
        input =>
          workflowContent.constants.find(
            constant =>
              constant.connector_id === input.connector_id &&
              constant.operator_id === input.operator_id
          ) === undefined && checkName(input.name, input.id) === false
      ) ||
      workflowContent.outputs.some(
        output =>
          workflowContent.constants.find(
            constant =>
              constant.connector_id === output.connector_id &&
              constant.operator_id === output.operator_id
          ) === undefined && checkName(output.name, output.id) === false
      )
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

    dialogRef
      .afterClosed()
      .pipe(
        switchMap(updatedComponentTransformation => {
          if (updatedComponentTransformation) {
            return this.baseItemService.updateTransformation(
              updatedComponentTransformation
            );
          }
          return of(null);
        })
      )
      .subscribe();
  }

  private configureWorkflowIO(workflowTransformation: WorkflowTransformation) {
    this.transformationStore
      .select(selectTransformationById(workflowTransformation.id))
      .pipe(first())
      .subscribe(selectedTransformation => {
        if (selectedTransformation === undefined) {
          return;
        }

        const dialogRef = this.dialog.open<
          WorkflowIODialogComponent,
          WorkflowIODialogData,
          | false
          | {
              inputs: IOConnector[];
              outputs: IOConnector[];
              constants: Constant[];
            }
        >(WorkflowIODialogComponent, {
          width: '95%',
          minHeight: '200px',
          data: {
            // TODO refactor all mutations in workflow dialog component and remove stringify.
            workflowTransformation: JSON.parse(
              JSON.stringify(selectedTransformation)
            ),
            editMode: selectedTransformation.state !== RevisionState.RELEASED,
            actionOk: 'Save',
            actionCancel: 'Cancel'
          }
        });

        dialogRef
          .afterClosed()
          .pipe(first())
          .subscribe(result => {
            if (result) {
              const inputIoConnectors: IOConnector[] = this._updateIoItemPositions(
                result.inputs,
                true,
                workflowTransformation
              );
              const outputIoConnectors: IOConnector[] = this._updateIoItemPositions(
                result.outputs,
                false,
                workflowTransformation
              );

              const ioConnectorIds = [...result.inputs, ...result.outputs].map(
                ioConnector =>
                  `${ioConnector.operator_id}_${ioConnector.connector_id}`
              );

              const innerLinks: Link[] = workflowTransformation.content.links.filter(
                link => {
                  let isOuterLink: boolean;
                  if (
                    Utils.isNullOrUndefined(link.start.operator) ||
                    Utils.isNullOrUndefined(link.end.operator)
                  ) {
                    isOuterLink = true;
                  } else {
                    const fromIoConnectorId = `${link.start.operator}_${link.start.connector.id}`;
                    const toIoConnectorId = `${link.end.operator}_${link.end.connector.id}`;
                    isOuterLink =
                      ioConnectorIds.includes(fromIoConnectorId) ||
                      ioConnectorIds.includes(toIoConnectorId);
                  }
                  return !isOuterLink;
                }
              );

              const links: Link[] = [
                ...innerLinks,
                ...this._createLinks(
                  inputIoConnectors,
                  outputIoConnectors,
                  result.constants
                )
              ];

              const updatedWorkflowTransformation: WorkflowTransformation = {
                ...workflowTransformation,
                content: {
                  ...workflowTransformation.content,
                  links,
                  inputs: inputIoConnectors,
                  outputs: outputIoConnectors,
                  constants: result.constants
                }
              };

              this.baseItemService
                .updateTransformation(updatedWorkflowTransformation)
                .subscribe();
            }
          });
      });
  }

  private _updateIoItemPositions(
    ioConnectors: IOConnector[],
    isInput: boolean,
    workflowTransformation: WorkflowTransformation
  ): IOConnector[] {
    return ioConnectors.map(ioConnector =>
      this._updateIoItemPosition(ioConnector, isInput, workflowTransformation)
    );
  }

  private _updateIoItemPosition(
    ioConnector: IOConnector,
    isInput: boolean,
    workflowTransformation: WorkflowTransformation
  ): IOConnector {
    const operator = workflowTransformation.content.operators.find(
      op => op.id === ioConnector.operator_id
    );
    if (operator === undefined) {
      throw new Error('Operator not found!');
    }
    let connectorIndex = operator.inputs.findIndex(
      cio => cio.id === ioConnector.connector_id
    );
    if (connectorIndex === -1) {
      connectorIndex = operator.outputs.findIndex(
        cio => cio.id === ioConnector.connector_id
      );
      if (connectorIndex === -1) {
        throw new Error('Connector not found!');
      }
    }

    return {
      ...ioConnector,
      position: {
        x: operator.position.x + (isInput ? -250 : 450),
        y: operator.position.y + 60 + connectorIndex * 30
      }
    };
  }

  private _createLinks(
    inputIoConnectors: IOConnector[],
    outputIoConnectors: IOConnector[],
    constants: Constant[]
  ): Link[] {
    const isConnectedIoConnector = (ioConnector: IOConnector) =>
      !Utils.string.isEmptyOrUndefined(ioConnector.name);

    const inputLinks = inputIoConnectors
      .filter(isConnectedIoConnector)
      .map(ioItem => this._createInputLink(ioItem));

    const outputLinks = outputIoConnectors
      .filter(isConnectedIoConnector)
      .map(ioItem => this._createOutputLink(ioItem));

    const constantLinks = constants.map(constant =>
      this._createInputLink(constant)
    );

    return [...inputLinks, ...outputLinks, ...constantLinks];
  }

  private _createInputLink(io: IOConnector | Constant): Link {
    return {
      // TODO is this okay for constant links? because currently in constant links link.id === start.connector.id
      id: uuid().toString(),
      start: {
        connector: {
          id: io.id,
          name: io.name,
          data_type: io.data_type,
          position: io.position
        }
      },
      end: {
        operator: io.operator_id,
        connector: {
          id: io.connector_id,
          name: io.connector_name,
          data_type: io.data_type,
          position: {
            x: 0,
            y: 0
          }
        }
      },
      path: []
    };
  }

  private _createOutputLink(io: IOConnector): Link {
    return {
      id: uuid().toString(),
      start: {
        operator: io.operator_id,
        connector: {
          id: io.connector_id,
          // TODO backend sets wrong connector name "connector_name" in workflowContent.outputs
          name: io.connector_name,
          data_type: io.data_type,
          position: {
            x: 0,
            y: 0
          }
        }
      },
      end: {
        connector: {
          id: io.id,
          name: io.name,
          data_type: io.data_type,
          position: io.position
        }
      },
      path: []
    };
  }
}
