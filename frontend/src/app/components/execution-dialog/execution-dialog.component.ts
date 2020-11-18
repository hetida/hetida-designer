import { DatePipe } from '@angular/common';
import {
  ChangeDetectionStrategy,
  ChangeDetectorRef,
  Component,
  Inject,
  OnInit
} from '@angular/core';
import {
  AbstractControl,
  FormArray,
  FormBuilder,
  FormGroup,
  ValidationErrors,
  ValidatorFn
} from '@angular/forms';
import {
  MatDialog,
  MatDialogRef,
  MAT_DIALOG_DATA
} from '@angular/material/dialog';
import { IOType } from 'hetida-flowchart';
import { iif, Observable, of, Subject } from 'rxjs';
import { switchMap, switchMapTo, tap } from 'rxjs/operators';
import { AbstractBaseItem } from 'src/app/model/base-item';
import { ComponentBaseItem } from 'src/app/model/component-base-item';
import { IOItem } from 'src/app/model/io-item';
import { WorkflowBaseItem } from 'src/app/model/workflow-base-item';
import { ComponentEditorService } from 'src/app/service/component-editor.service';
import {
  AdapterHttpService,
  AdapterResponse,
  DataSourceSink
} from 'src/app/service/http-service/adapter-http.service';
import {
  InputWiring,
  OutputWiring,
  Wiring,
  WiringDateRangeFilter,
  WiringHttpService
} from 'src/app/service/http-service/wiring-http.service';
import { WorkflowEditorService } from 'src/app/service/workflow-editor.service';
import { Utils } from 'src/app/utils/utils';
import { v4 as UUID } from 'uuid';
import { BaseItemType } from '../../enums/base-item-type';
import { ConfirmDialogComponent } from '../confirmation-dialog/confirm-dialog.component';
import {
  ExecutionContextMenuData,
  ExecutionDialogContextMenuComponent,
  WiringChangeEvent
} from '../execution-dialog-context-menu/execution-dialog-context-menu.component';
import {
  JsonEditorComponent,
  JsonEditorModalData
} from '../json-editor/json-editor.component';
import {
  AdapterTreeModalData,
  TreeNodeModalComponent
} from '../tree-node-modal/tree-node-modal.component';
import {
  TreeNodeItemClickEvent,
  TreeNodeSourceType
} from '../tree-node/tree-node.component';

export interface ExecutionDialogData {
  title: string;
  abstractBaseItem: AbstractBaseItem;
}

export interface UiItemWiring {
  id: string;
  ioItemName: string;
  ioItemId: string;
  rawValue?: string | null | undefined;
  nodeId?: string | null | undefined;
  dataType: string;
  timestampRange?: string[];
  isSource: boolean;
}

type SourceType = 'INPUT_WIRING' | 'OUTPUT_WIRING';

@Component({
  selector: 'hd-execution-dialog',
  templateUrl: './execution-dialog.component.html',
  styleUrls: ['./execution-dialog.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush,
  providers: [DatePipe]
})
export class ExecutionDialogComponent implements OnInit {
  readonly STANDARD_WORKFLOW_NAME = 'STANDARD-WIRING';

  private readonly SOURCE_TYPE: SourceType = 'INPUT_WIRING';
  private readonly SINK_TYPE: SourceType = 'OUTPUT_WIRING';

  adapterResponse: AdapterResponse;
  thingSourcesMap: Map<string, DataSourceSink> = new Map();
  thingSinksMap: Map<string, DataSourceSink> = new Map();
  wiring: Wiring;

  inputOutputForm: FormGroup;
  abstractBaseItem: AbstractBaseItem;

  // If the JSON file cannot be parsed, this observable will
  // be used to show error state.
  jsonImportErrorStatus = new Subject<string>();
  adapterAvailable = false;

  get inputFormArray(): FormArray {
    return this.inputOutputForm.get('inputs') as FormArray;
  }

  get outputFormArray(): FormArray {
    return this.inputOutputForm.get('outputs') as FormArray;
  }

  constructor(
    private readonly dialogRef: MatDialogRef<ConfirmDialogComponent>,
    @Inject(MAT_DIALOG_DATA) public readonly data: ExecutionDialogData,
    private readonly workflowService: WorkflowEditorService,
    private readonly componentService: ComponentEditorService,
    private readonly adapterHttpService: AdapterHttpService,
    private readonly wiringHttpService: WiringHttpService,
    private readonly formBuilder: FormBuilder,
    private readonly dialog: MatDialog,
    private readonly changeDetector: ChangeDetectorRef,
    private readonly dateFormatter: DatePipe
  ) {}

  ngOnInit() {
    this.abstractBaseItem = this.data.abstractBaseItem;

    const getAdapterList$ = this.adapterHttpService.getAdapter();
    const getAdapter$ = this.adapterHttpService.getOneAdapter(2);

    // The manual input adapter (no binding to external data source) has always index 0.
    getAdapterList$
      .pipe(
        tap(adapters =>
          adapters.length > 1
            ? (this.adapterAvailable = true)
            : (this.adapterAvailable = false)
        ),
        switchMap(adapters =>
          iif(
            () => !!adapters.find(adapter => adapter.id === 2),
            getAdapter$,
            of(false)
          )
        )
      )
      .subscribe(adapter => {
        if (adapter) {
          this.adapterResponse = adapter as AdapterResponse;

          this.thingSourcesMap = this.adapterResponse.sources.reduce(
            (map, obj) => {
              return map.set(obj.id, obj);
            },
            new Map<string, DataSourceSink>()
          );

          this.thingSinksMap = this.adapterResponse.sinks.reduce((map, obj) => {
            return map.set(obj.id, obj);
          }, new Map<string, DataSourceSink>());
        }
        this.inputOutputForm = this.createExecutionDialogForm(
          this.abstractBaseItem
        );
        this.changeDetector.detectChanges();
      });
  }

  private createExecutionDialogForm(
    abstractBaseItem: AbstractBaseItem
  ): FormGroup {
    // We will take the first wiring, for the moment being only a single wiring may be present.
    Utils.assert((abstractBaseItem.wirings ?? []).length <= 1);
    const wiring: Wiring | undefined = abstractBaseItem.wirings?.find(
      wiringCandidate => wiringCandidate.name === this.STANDARD_WORKFLOW_NAME
    );

    const inputFormArray = abstractBaseItem.inputs
      .filter(input => Utils.isDefined(input.name))
      .map(input => {
        const foundWiring: InputWiring | undefined = wiring?.inputWirings.find(
          wiringCandidate => input.name === wiringCandidate.workflowInputName
        );
        return this.createInputOrOutputForm(
          input,
          this.SOURCE_TYPE,
          foundWiring
        );
      });

    const outputFormArray = abstractBaseItem.outputs.map(input => {
      const existingOutputWiring:
        | OutputWiring
        | undefined = wiring?.outputWirings.find(
        wiringCandidate => input.name === wiringCandidate.workflowOutputName
      );
      return this.createInputOrOutputForm(
        input,
        this.SINK_TYPE,
        existingOutputWiring
      );
    });

    return this.formBuilder.group({
      inputs: new FormArray(inputFormArray),
      outputs: new FormArray(outputFormArray)
    });
  }

  private createInputOrOutputForm(
    ioItem: IOItem,
    sourceType: SourceType,
    inputOrOutputWiring?: InputWiring | OutputWiring
  ): FormGroup {
    let nodeId: string = null;
    let manualValue: string = null;
    let timestampFrom: Date = null;
    let timestampTo: Date = null;
    let timestampMin: Date = null;
    let timestampMax: Date = null;

    if (inputOrOutputWiring && sourceType === 'INPUT_WIRING') {
      const tmpInputWiring = inputOrOutputWiring as InputWiring;
      // For some reason it can be happen that the nodeId disappears from the DB. If
      // that happens do not use the nodeId from wiring.
      nodeId = this.thingSourcesMap.has(tmpInputWiring.sourceId)
        ? tmpInputWiring.sourceId
        : null;

      if (tmpInputWiring.filters) {
        manualValue = tmpInputWiring.filters.value;
        timestampFrom = new Date(tmpInputWiring.filters.timestampFrom);
        timestampTo = new Date(tmpInputWiring.filters.timestampTo);

        const sourceNode = this.thingSourcesMap.get(nodeId);
        if (sourceNode && typeof nodeId === 'string') {
          if (AdapterHttpService.isDateFilter(sourceNode.filters)) {
            timestampMin = new Date(sourceNode.filters.fromTimestamp.min);
            timestampMax = new Date(sourceNode.filters.toTimestamp.max);
          }
        }
      }
    } else if (
      inputOrOutputWiring &&
      AdapterHttpService.isOutputWiring(inputOrOutputWiring)
    ) {
      nodeId = this.thingSinksMap.has(inputOrOutputWiring.sinkId)
        ? inputOrOutputWiring.sinkId
        : null;
    }

    const formGroup = this.formBuilder.group({
      id: inputOrOutputWiring ? inputOrOutputWiring.id : null,
      ioItemName: ioItem.name,
      ioItemId: ioItem.id,
      rawValue: [manualValue],
      nodeId,
      dataType: ioItem.type,
      timestampRange: [[timestampFrom, timestampTo]],
      timestampRangeFilter: [[timestampMin, timestampMax]],
      isSource: Utils.isDefined(nodeId)
    });

    if (sourceType === 'INPUT_WIRING') {
      formGroup.get('nodeId').setValidators(this.nodeIdValidation(formGroup));

      formGroup
        .get('rawValue')
        .setValidators(
          this.inputTypeCheckIfAny(ioItem.type as IOType, formGroup)
        );

      if ((ioItem.type as IOType) === IOType.SERIES) {
        formGroup
          .get('timestampRange')
          .setValidators(this.timestampRangeValidation(formGroup));
      }
    }

    return formGroup;
  }

  timestampRangeValidation(formGroup: FormGroup) {
    return (control: AbstractControl): ValidationErrors | null => {
      if (!formGroup.get('nodeId').value) {
        return null;
      }

      const [fromTimeRange, toTimeRange]: [
        Date | null,
        Date | null
      ] = control.value;

      if (!fromTimeRange || !toTimeRange) {
        return {
          noTimeRange: {
            value: control.value
          },
          message: 'time range is invalid'
        };
      }

      if (isNaN(fromTimeRange.getTime()) || isNaN(toTimeRange.getTime())) {
        return {
          noTimeRange: {
            value: control.value
          },
          message: 'time range is invalid'
        };
      }

      return null;
    };
  }

  nodeIdValidation(fromGroup: FormGroup): ValidatorFn {
    return (control: AbstractControl): ValidationErrors | null => {
      let validationErrorOrNull: ValidationErrors | null = null;
      // If Source is set to "manual" do not validate nodeId
      if (!fromGroup.get('isSource').value) {
        return validationErrorOrNull;
      }

      if (Utils.isNullOrUndefined(control.value)) {
        validationErrorOrNull = {
          missingSource: true,
          message: 'Missing Source'
        };
        return validationErrorOrNull;
      }

      return validationErrorOrNull;
    };
  }

  /**
   * Validates input
   */
  inputTypeCheckIfAny(ioItemType: IOType, formGroup: FormGroup): ValidatorFn {
    return (control: AbstractControl): ValidationErrors | null => {
      let validationErrorIfAny = null;
      const controlValue = control.value as string | null | undefined;

      // If InputType is on "source" do not validate "rawValue".
      if (formGroup.get('isSource').value) {
        return validationErrorIfAny;
      }

      const ioItemTypeOrControlValueIsUndefined = Utils.isNullOrUndefined(
        ioItemType
      );
      const stringIsEmpty = Utils.string.isEmptyOrUndefined(controlValue);

      if (ioItemTypeOrControlValueIsUndefined || stringIsEmpty) {
        validationErrorIfAny = {
          invalidType: {
            value: control.value
          },
          message: 'please enter a value'
        };
        return validationErrorIfAny;
      }

      switch (ioItemType) {
        case IOType.STRING:
          break;
        case IOType.BOOLEAN:
          const isBooleanValue =
            controlValue === 'True' || controlValue === 'False';
          if (!isBooleanValue) {
            validationErrorIfAny = {
              invalidType: {
                value: control.value
              },
              message: 'use True or False'
            };
            return validationErrorIfAny;
          }
          break;
        case IOType.INT:
          if (!Utils.isInteger(controlValue)) {
            validationErrorIfAny = {
              invalidType: {
                value: control.value
              },
              message: 'not integer value'
            };
          }
          break;
        case IOType.FLOAT:
          if (!Utils.isFloat(controlValue)) {
            validationErrorIfAny = {
              invalidType: {
                value: control.value
              },
              message: 'not float value'
            };
          }
          break;
        case IOType.SERIES:
        case IOType.PLOTLYJSON:
        case IOType.DATAFRAME:
          try {
            JSON.parse(controlValue);
          } catch (error) {
            validationErrorIfAny = {
              invalidType: {
                value: control.value
              },
              message: 'invalid JSON'
            };
          }
          break;
        default:
      }
      return validationErrorIfAny;
    };
  }

  getTypeColor(type: string): string {
    return `var(--${type}-color)`;
  }

  isTimeSeriesType(type: string): boolean {
    return type === IOType.SERIES;
  }

  toggleConstant(inputControl: AbstractControl) {
    const isSourceControl = inputControl.get('isSource');
    isSourceControl.setValue(!isSourceControl.value);

    if (isSourceControl.value) {
      inputControl.get('rawValue').reset();
    } else {
      inputControl.get('nodeId').reset();
      inputControl.get('timestampRange').reset([null, null]);
    }
  }

  openAdapterTreeDialog(dataSourceType: TreeNodeSourceType, ioType: IOType) {
    const data: AdapterTreeModalData = {
      sourcesOrSinks:
        dataSourceType === 'sink'
          ? this.adapterResponse.sinks
          : this.adapterResponse.sources,
      thingNodes: this.adapterResponse.thingNodes,
      dataSourceType,
      initialDataTypeFilter: ioType
    };
    const dialog = this.dialog.open<
      TreeNodeModalComponent,
      AdapterTreeModalData,
      never
    >(TreeNodeModalComponent, {
      width: '700px',
      data
    });

    dialog.componentInstance.dataSourceSelect.subscribe(
      treeNodeItemClickEvent => {
        this.openWireAttributeToDataMenu(treeNodeItemClickEvent);
        this.changeDetector.markForCheck();
      }
    );
  }

  openWireAttributeToDataMenu(treeNodeItemClickEvent: TreeNodeItemClickEvent) {
    // the node from tree
    const node = treeNodeItemClickEvent.node;
    // Is this a sink or source?
    const dataSourceType = treeNodeItemClickEvent.dataSourceType;
    let ioItems: UiItemWiring[];

    if (dataSourceType === 'source') {
      const formInputArray = this.inputOutputForm.get('inputs');
      Utils.assert(formInputArray instanceof FormArray);
      ioItems = formInputArray.getRawValue();
    } else if (dataSourceType === 'sink') {
      const formOutputArray = this.inputOutputForm.get('outputs');
      Utils.assert(formOutputArray instanceof FormArray);
      ioItems = formOutputArray.getRawValue();
    }

    // Only items of source type = adapter are selectable.
    ioItems = ioItems.filter(ioItem => ioItem.isSource);

    const dialog = this.dialog.open<
      ExecutionDialogContextMenuComponent,
      ExecutionContextMenuData,
      never
    >(ExecutionDialogContextMenuComponent, {
      width: '300px',
      disableClose: false,
      backdropClass: 'contextDropDown',
      position: {
        top: `${treeNodeItemClickEvent.event.clientY}px`,
        left: `${treeNodeItemClickEvent.event.clientX}px`
      },
      data: {
        dataOrigin: node,
        IOItem: ioItems
      }
    });

    dialog.componentInstance.wiringChange.subscribe(
      (idAndChecked: WiringChangeEvent) => {
        let inputOrOutputControls: AbstractControl[];
        if (dataSourceType === 'source') {
          inputOrOutputControls = this.inputFormArray.controls;
        } else if (dataSourceType === 'sink') {
          inputOrOutputControls = this.outputFormArray.controls;
        }

        const foundIoItemControl = inputOrOutputControls.find(
          control => control.value.ioItemId === idAndChecked.ioItemId
        );

        const realFilters = node.filters;
        if (AdapterHttpService.isDateFilter(realFilters)) {
          const timestampMin = new Date(realFilters.fromTimestamp.min);
          const timestampMax = new Date(realFilters.toTimestamp.max);
          foundIoItemControl
            .get('timestampRangeFilter')
            .setValue([timestampMin, timestampMax]);
        }
        foundIoItemControl
          .get('nodeId')
          .setValue(idAndChecked.checked ? node.id : null);
        foundIoItemControl.get('rawValue').reset();
        this.changeDetector.markForCheck();
      }
    );
  }

  onCancel(): void {
    this.dialogRef.close();
  }

  onOk(): void {
    this.inputFormArray.markAllAsTouched();
    if (this.inputFormArray.invalid) {
      return;
    }

    const abstractBaseItem = this.data.abstractBaseItem;
    let isUpdate = false;

    const foundStandardWiring = abstractBaseItem.wirings.find(
      wiring => (wiring.name = this.STANDARD_WORKFLOW_NAME)
    );
    // If we have a standard wiring, we would update that entity.
    if (foundStandardWiring) {
      isUpdate = true;
    }

    const reassembledWorkflowWiring: Wiring = {
      id: foundStandardWiring ? foundStandardWiring.id : UUID().toString(),
      name: this.STANDARD_WORKFLOW_NAME,
      inputWirings: null,
      outputWirings: null
    };

    const inputWirings: InputWiring[] = this.inputFormArray.controls.map(
      (control: AbstractControl) => {
        Utils.assert(
          control instanceof FormGroup,
          'Form schema is flawed, formGroup after formArray not found.'
        );
        const uiWiring: UiItemWiring = control.getRawValue() ?? null;
        let filters: WiringDateRangeFilter = {};

        if (uiWiring.rawValue !== undefined) {
          filters.value = uiWiring.rawValue;
        }

        // Apply timestamp only for series and for non manual selection.
        if (
          uiWiring.dataType === IOType.SERIES &&
          Utils.isNullOrUndefined(uiWiring.rawValue)
        ) {
          filters = {
            timestampFrom: this.dateFormatter.transform(
              uiWiring.timestampRange[0],
              `yyyy-MM-dd'T'HH:mm:ss.SSSSSSSSS'Z'`,
              '+0000'
            ),
            timestampTo: this.dateFormatter.transform(
              uiWiring.timestampRange[1],
              `yyyy-MM-dd'T'HH:mm:ss.SSSSSSSSS'Z'`,
              '+0000'
            )
          };
        }

        // The adapter id can be 1 or 2, it is depending on input type (manual or from source).
        const tmpAdapterId =
          uiWiring.nodeId !== undefined && uiWiring.nodeId !== null ? 2 : 1;
        return {
          id: uiWiring.id ?? UUID().toString(),
          workflowInputName: uiWiring.ioItemName,
          adapterId: tmpAdapterId,
          sourceId: uiWiring.nodeId,
          filters
        };
      }
    );

    const outputWirings: OutputWiring[] = this.outputFormArray.controls.map(
      control => {
        Utils.assert(
          control instanceof FormGroup,
          'Form schema is flawed, formGroup after formArray not found'
        );

        const uiWiring: UiItemWiring = control.getRawValue();
        return {
          id: uiWiring.id ?? UUID().toString(),
          workflowOutputName: uiWiring.ioItemName,
          adapterId: Utils.isDefined(uiWiring.nodeId) ? 2 : 1,
          sinkId: uiWiring.nodeId
        };
      }
    );

    reassembledWorkflowWiring.inputWirings = inputWirings;
    reassembledWorkflowWiring.outputWirings = outputWirings;

    let updateOrSave$: Observable<Wiring>;
    if (isUpdate) {
      updateOrSave$ = this.wiringHttpService.updateWiring(
        reassembledWorkflowWiring
      );
    } else {
      updateOrSave$ = this.wiringHttpService.saveWiring(
        reassembledWorkflowWiring
      );
    }

    updateOrSave$
      .pipe(
        switchMapTo(
          iif(
            () => this.abstractBaseItem.type === BaseItemType.WORKFLOW,
            this._executeTestWorkflow(reassembledWorkflowWiring),
            this._executeTestComponent(reassembledWorkflowWiring)
          )
        )
      )
      .subscribe();

    this.dialogRef.close();
  }

  private _executeTestWorkflow(wiring: Wiring): Observable<WorkflowBaseItem> {
    return this.workflowService
      .bindWiringToWorkflow(this.abstractBaseItem.id, wiring)
      .pipe(
        switchMap(() =>
          this.workflowService.testWorkflow(this.abstractBaseItem.id, wiring)
        )
      );
  }

  private _executeTestComponent(wiring: Wiring): Observable<ComponentBaseItem> {
    return this.componentService
      .bindWiringToComponent(this.abstractBaseItem.id, wiring)
      .pipe(
        switchMap(() =>
          this.componentService.testComponent(this.abstractBaseItem.id, wiring)
        )
      );
  }

  openJsonEditorModal(inputControl: AbstractControl) {
    let rawValue = inputControl.get('rawValue').value;
    if (!rawValue) {
      rawValue = JSON.stringify(
        this.getExampleValueForIoType(IOType.SERIES),
        null,
        4
      );
    }

    const data: JsonEditorModalData = {
      value: rawValue,
      dataType: inputControl.get('dataType').value,
      actionOk: 'Save',
      actionCancel: 'Cancel',
      title: `Json input for ${inputControl.get('ioItemName').value}`
    };
    const dialog = this.dialog.open<
      JsonEditorComponent,
      JsonEditorModalData,
      string
    >(JsonEditorComponent, {
      width: '600px',
      data
    });

    dialog.afterClosed().subscribe((json: string) => {
      inputControl.get('rawValue').setValue(json);
    });
  }

  uploadJsonForAllInputs(jSONInput: HTMLInputElement) {
    jSONInput.click();
  }

  downloadJsonSchema() {
    const fileName = `jsonschema_${this.abstractBaseItem.name}_${this.abstractBaseItem.tag}.json`;
    const schema = this._generateJSONSchema(true);
    const data = new Blob([JSON.stringify(schema, null, 4)], {
      type: 'application/json'
    });

    const tmpElement = document.createElement('a');
    tmpElement.setAttribute('download', fileName);

    tmpElement.href = window.URL.createObjectURL(data);

    tmpElement.style.display = 'none';
    document.body.appendChild(tmpElement);

    tmpElement.click();
    document.body.removeChild(tmpElement);
  }

  /**
   * Generate a json schema that works as a layout for the component
   */
  private _generateJSONSchema(
    withExampleData: boolean = false
  ): {
    [i: string]: any;
  } {
    const generatedJsonSchema: {
      [key: string]: any;
    } = {};

    this.inputFormArray.controls.forEach(control => {
      const inputName = control.get('ioItemName').value as string;
      const ioDataType = control.get('dataType').value as IOType;
      if (withExampleData) {
        generatedJsonSchema[inputName] = this.getExampleValueForIoType(
          ioDataType
        );
      } else {
        generatedJsonSchema[inputName] = null;
      }
    });
    return generatedJsonSchema;
  }

  // noinspection JSMethodCanBeStatic
  /**
   *
   * Returns an example value, based on dataType
   * Will be used to fill the json schema template
   *
   * @param ioDataType dataType
   */
  private getExampleValueForIoType(ioDataType: IOType) {
    let exampleValue = null;
    switch (ioDataType) {
      case IOType.BOOLEAN:
        exampleValue = false;
        break;
      case IOType.FLOAT:
        exampleValue = 1.23;
        break;
      case IOType.INT:
        exampleValue = 123;
        break;
      case IOType.STRING:
        exampleValue = 'dummy';
        break;
      case IOType.SERIES:
        exampleValue = {
          '2020-01-01T01:15:27.000Z': 42.2,
          '2020-01-03T08:20:03.000Z': 18.7,
          '2020-01-03T08:20:04.000Z': 25.9
        };
        break;
      case IOType.DATAFRAME:
        exampleValue = {
          column1: {
            '2019-08-01T15:45:36.000Z': 1.0,
            '2019-08-02T11:33:41.000Z': 2.0
          },
          column2: {
            '2019-08-01T15:45:36.000Z': 1.3,
            '2019-08-02T11:33:41.000Z': 2.8
          }
        };
        break;
      case IOType.ANY:
        exampleValue = {
          a: true,
          b: 31.56
        };
        break;
      default:
    }

    return exampleValue;
  }

  triggerForAllInputs(jSONInput: HTMLInputElement) {
    const uploadedFile = jSONInput.files.item(0);
    const fileReader = new FileReader();

    fileReader.onload = () => {
      const textJson = fileReader.result as string;
      try {
        const importedJson = JSON.parse(textJson);
        this.inputFormArray.controls.forEach(inputControl => {
          const foundAttribute =
            importedJson[inputControl.get('ioItemName').value];
          if (Utils.isDefined(foundAttribute)) {
            inputControl.get('isSource').setValue(false);
            inputControl.get('nodeId').reset(null);
            inputControl
              .get('rawValue')
              .setValue(
                typeof foundAttribute === 'string'
                  ? foundAttribute
                  : JSON.stringify(foundAttribute, null, 4)
              );
          } else {
            // TODO display a warning, because in importedJson are missing input fields.
          }

          inputControl.get('rawValue').markAllAsTouched();
          this.changeDetector.markForCheck();
        });
        this.jsonImportErrorStatus.next('');
      } catch (error) {
        this.jsonImportErrorStatus.next('JSON is malformed.');
        this.changeDetector.markForCheck();
      }
    };

    fileReader.readAsText(uploadedFile);

    // remove uploaded data from input element
    // otherwise files with same name will don´t uploaded again.
    jSONInput.value = '';
  }

  isJsonType(ioType: IOType): boolean {
    let isJsonType = false;
    if (
      // tslint:disable-next-line: prefer-switch
      ioType === IOType.SERIES ||
      ioType === IOType.DATAFRAME ||
      ioType === IOType.ANY
    ) {
      isJsonType = true;
    }

    return isJsonType;
  }

  clearOutput(outputControl: AbstractControl) {
    outputControl.get('nodeId').reset(null);
  }

  clearInput(inputControl: AbstractControl) {
    inputControl.get('isSource').reset(false);
    inputControl.get('rawValue').reset(null);
    inputControl.get('nodeId').reset(null);
    inputControl.get('timestampRange').reset([null, null]);
  }
}
