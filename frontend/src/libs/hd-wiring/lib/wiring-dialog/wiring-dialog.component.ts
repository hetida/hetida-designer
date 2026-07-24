import { DatePipe } from '@angular/common';
import {
  ChangeDetectionStrategy,
  ChangeDetectorRef,
  Component,
  EventEmitter,
  Inject,
  Input,
  OnInit,
  Optional,
  Output
} from '@angular/core';
import {
  AbstractControl,
  FormArray,
  FormBuilder,
  FormGroup,
  ValidationErrors,
  ValidatorFn
} from '@angular/forms';
import { MAT_DIALOG_DATA, MatDialog } from '@angular/material/dialog';
import { IOType, IOTypeOption } from 'hetida-flowchart';
import moment, { Moment } from 'moment';
import { combineLatest, Observable, of, Subject } from 'rxjs';
import { catchError, map, startWith, switchMap, tap } from 'rxjs/operators';
import {
  Adapter,
  AdapterDataType,
  AdapterHttpService,
  DataStructureType,
  InputFilters,
  InputOrOutputWiring,
  InputWiring,
  MetaData,
  NodeSourceType,
  OutputWiring,
  SourceSinkNode,
  TestWiring,
  ThingNode
} from '../adapter-http.service';
import { ConfigService } from '../config.service';
import { JsonEditorComponent, JsonEditorModalData } from '../json-editor';
import {
  MetaDataWiringChangeEvent,
  MetaDataWiringModalComponent,
  MetadataWiringModalData
} from '../meta-data-wiring-modal';
import { NodeClickEvent } from '../node-click/node-click';
import {
  ExecutionContextMenuData,
  NodeWiringContextMenuComponent,
  WiringChangeEvent
} from '../node-wiring-context-menu';
import {
  AdapterTreeModalData,
  TreeNodeModalComponent
} from '../tree-node-modal';
import { OptionalMembers, Utils } from '../utils/utils';
import { WarningDialogComponent } from '../warning-dialog/warning-dialog.component';

export interface ExecutionDialogData {
  title: string;
  wiringItem: WiringItem;
  adapterList: Adapter[];
}

export interface ConfirmClickEvent {
  id: any;
  test_wiring: TestWiring;
}

export interface UiItemWiring {
  ioItemName: string;
  ioItemId: string;
  rawValue?: string | null | undefined;
  nodeId?: string | null | undefined;
  nodeName: string | null;
  displayName: string | null;
  nodeType: AdapterDataType;
  metaDataKey?: string | null | undefined;
  refIdType?: NodeSourceType;
  ioType: IOType;
  timestampRange?: [dateMin: Moment | null, dateMax: Moment | null];
  timestampRangeQuery?: string | null;
  timestampRangeFilter?: [dateMin: Moment | null, dateMax: Moment | null];
  timestampRangePickerHidden?: boolean;
  adapterId: string;
  textFilters: [] | FormArray;
  type: IOTypeOption;
  defaultValue: string | undefined;
  useDefaultValue: boolean;
}

export interface IO {
  id: string;
  name: string;
  data_type: IOType;
  value?: string;
  type: IOTypeOption;
  exposed?: boolean;
}

export interface IoInterface {
  inputs: IO[];
  outputs: IO[];
}

export interface WiringItem {
  id: string;
  test_wiring: TestWiring;
  io_interface: IoInterface;
  name?: string;
  version_tag?: string;
}

export interface FreeTextFilter {
  name: string;
  type: string;
  required: boolean;
  value?: string;
  default_value?: string;
}

export interface TextFilter extends FreeTextFilter {
  key: string;
}

interface DialogPositionAndMaxHeight {
  position: {
    top?: string;
    bottom?: string;
    left?: string;
    right?: string;
  };
  maxHeight: string;
}

type SourceType = 'INPUT_WIRING' | 'OUTPUT_WIRING';
type SourcesSinksHash = { [id: string]: SourceSinkNode | ThingNode };

@Component({
  selector: 'hd-wiring-dialog',
  templateUrl: './wiring-dialog.component.html',
  styleUrls: ['./wiring-dialog.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush,
  providers: [DatePipe],
  standalone: false
})
export class WiringDialogComponent implements OnInit {
  get inputFormArray(): FormArray {
    return this.inputOutputForm.get('inputs') as FormArray;
  }

  get outputFormArray(): FormArray {
    return this.inputOutputForm.get('outputs') as FormArray;
  }

  constructor(
    @Optional()
    @Inject(MAT_DIALOG_DATA)
    public readonly data: ExecutionDialogData,
    public readonly _configService: ConfigService,
    private readonly adapterHttpService: AdapterHttpService,
    private readonly formBuilder: FormBuilder,
    private readonly dialog: MatDialog,
    private readonly changeDetector: ChangeDetectorRef,
    private readonly dateFormatter: DatePipe
  ) {}

  @Input()
  title!: string;

  @Input()
  wiringItem!: WiringItem;

  @Input()
  adapterList!: Adapter[];

  @Output()
  cancelDialogClick = new EventEmitter<void>();

  @Output()
  confirmClick = new EventEmitter<ConfirmClickEvent>();
  private readonly SOURCE_TYPE: SourceType = 'INPUT_WIRING';
  private readonly SINK_TYPE: SourceType = 'OUTPUT_WIRING';

  inputOutputForm!: FormGroup;

  // If an error occurs during the upload operation,
  // this observable will be triggered.
  jsonImportErrorStatus = new Subject<string>();

  _timestampRangeQueryDelimiter = ',';
  _availableAdapters!: Adapter[];

  ngOnInit(): void {
    this.title ??= this.data.title;
    this.wiringItem ??= this.data.wiringItem;
    this.adapterList ??= this.data.adapterList;

    Utils.assert(this.title, 'no title provided');
    Utils.assert(this.wiringItem, 'no wiring item provided');
    Utils.assert(
      this.adapterList,
      'no adapters are provided, if you don`t have any adapter implemented yet, you can pass an empty array'
    );

    const standardWiring: TestWiring | undefined = this.wiringItem.test_wiring;

    of(this.adapterList)
      .pipe(
        tap(availableAdapters => {
          this._availableAdapters = availableAdapters;
        }),
        switchMap(availableAdapters => {
          const inputWiring = standardWiring?.input_wirings ?? [];
          const outputWiring = standardWiring?.output_wirings ?? [];
          const wirings: InputOrOutputWiring[] = [
            ...inputWiring,
            ...outputWiring
          ];
          const dataSourceSink$: Observable<
            SourceSinkNode | ThingNode | null
          >[] = wirings
            .filter(
              wiring =>
                Utils.isNullOrUndefined(wiring.ref_key) ||
                wiring.ref_id_type === 'THINGNODE'
            )
            .filter(
              wiring =>
                wiring.adapter_id !==
                  AdapterHttpService.MANUAL_INPUT_ADAPTER_ID &&
                wiring.adapter_id !== 'drop' &&
                wiring.adapter_id !== 'plot'
            )
            .map(wiring => {
              const adapterOfInputWiring = availableAdapters.find(
                availableAdapter => availableAdapter.id === wiring.adapter_id
              );
              Utils.assert(
                adapterOfInputWiring,
                `Adapter Id ${wiring.adapter_id} not found`
              );

              let getSourceSink$: Observable<SourceSinkNode | ThingNode | null>;
              const wiringRefId = wiring.ref_id;
              Utils.assert(
                wiringRefId,
                'a wiring must have a ref_id after initialization'
              ); // TODO make ref_id non optional ?
              switch (wiring.ref_id_type) {
                case 'SOURCE':
                  getSourceSink$ = this.adapterHttpService.getOneSource(
                    wiringRefId,
                    adapterOfInputWiring.url
                  );
                  break;
                case 'SINK':
                  getSourceSink$ = this.adapterHttpService.getOneSink(
                    wiringRefId,
                    adapterOfInputWiring.url
                  );
                  break;
                case 'THINGNODE':
                  getSourceSink$ = this.adapterHttpService
                    .getNodesOfAdapter(adapterOfInputWiring.url, wiring.ref_id)
                    .pipe(
                      switchMap(adaptorData => {
                        let foundSourceOrSink:
                          | SourceSinkNode
                          | ThingNode
                          | null
                          | undefined;
                        if ('workflow_output_name' in wiring) {
                          foundSourceOrSink = adaptorData.sinks.find(
                            sink => sink.metadataKey === wiring.ref_key
                          );
                        } else if ('workflow_input_name' in wiring) {
                          foundSourceOrSink = adaptorData.sources.find(
                            source => source.metadataKey === wiring.ref_key
                          );
                        }
                        return new Observable<
                          SourceSinkNode | ThingNode | null
                        >(observer => {
                          if (foundSourceOrSink) {
                            observer.next(foundSourceOrSink);
                            observer.complete();
                          } else {
                            observer.error(wiring);
                          }
                        });
                      })
                    );
                  break;
                default:
                  throw new Error('Fetching for thing node is nor required');
              }
              return getSourceSink$.pipe(
                catchError(error => {
                  this._openSourceSinkOrThingNodeInfoMissingDialog(error);
                  return of(null);
                })
              );
            });
          // If no wiring is found
          if (dataSourceSink$.length === 0) {
            return of({});
          }

          return combineLatest(dataSourceSink$).pipe(
            map(wiringInputSource => {
              return wiringInputSource.reduce((acc, inputSource) => {
                if (inputSource) {
                  acc[inputSource.id] = inputSource;
                }
                return acc;
              }, {} as SourcesSinksHash);
            })
          );
        })
      )
      .subscribe(sourcesSinksHash => {
        this.inputOutputForm = this._createExecutionDialogForm(
          standardWiring,
          this.wiringItem.io_interface.inputs,
          this.wiringItem.io_interface.outputs,
          sourcesSinksHash
        );
        this.changeDetector.detectChanges();
      });
  }

  _checkFormGroupOrFail(control: AbstractControl): FormGroup {
    Utils.assert(control instanceof FormGroup);
    return control;
  }

  _getControlOrFail(
    abstractControl: AbstractControl,
    key: string
  ): AbstractControl {
    const controlOrNull = abstractControl.get(key);
    Utils.assert(
      controlOrNull,
      `Form control member with key ${key} is not defined.`
    );
    return controlOrNull;
  }

  private _createExecutionDialogForm(
    standardWiring: TestWiring | undefined,
    inputItems: IO[],
    outputItems: IO[],
    sourcesTransformationHash: SourcesSinksHash
  ): FormGroup {
    const inputFormArray = inputItems.map(inputItem => {
      const foundWiring: InputWiring | undefined =
        standardWiring?.input_wirings.find(
          wiringCandidate =>
            inputItem.name === wiringCandidate.workflow_input_name
        );
      return this.createInputOrOutputForm(
        inputItem,
        this.SOURCE_TYPE,
        foundWiring,
        sourcesTransformationHash
      );
    });

    const outputFormArray = outputItems.map(output => {
      const existingOutputWiring: OutputWiring | undefined =
        standardWiring?.output_wirings.find(
          wiringCandidate =>
            output.name === wiringCandidate.workflow_output_name
        );
      return this.createInputOrOutputForm(
        output,
        this.SINK_TYPE,
        existingOutputWiring,
        sourcesTransformationHash
      );
    });

    return this.formBuilder.group({
      inputs: new FormArray(inputFormArray),
      outputs: new FormArray(outputFormArray)
    });
  }

  // eslint-disable-next-line complexity
  private createInputOrOutputForm(
    ioItem: IO,
    sourceType: SourceType,
    inputOrOutputWiring: InputOrOutputWiring | undefined,
    nodesHash: SourcesSinksHash
  ): FormGroup {
    // Runs for every input or output ones.
    let nodeId: string | null = null;
    let manualValue: string | null = null;
    let timestampFrom: Moment | null = null;
    let timestampTo: Moment | null = null;
    let timestampRangeQuery: string | null = null;
    let timestampMin: Moment | null = null;
    let timestampMax: Moment | null = null;
    let timestampRangePickerHidden = false;
    let nodeName: string | null = null;
    let textFilters: TextFilter[] = [];
    let adapterId: string | null =
      sourceType === 'INPUT_WIRING'
        ? AdapterHttpService.MANUAL_INPUT_ADAPTER_ID
        : null;
    let useDefaultValue: boolean = ioItem.type === IOTypeOption.OPTIONAL;
    if (inputOrOutputWiring) {
      nodeId = inputOrOutputWiring.ref_id ?? null;
      adapterId = inputOrOutputWiring.adapter_id ?? null;
      if (
        inputOrOutputWiring.adapter_id !==
        AdapterHttpService.MANUAL_INPUT_ADAPTER_ID
      ) {
        // prettier-ignore
        nodeName = Utils.isDefined(nodeId)
          ? (nodesHash[nodeId]?.name ?? inputOrOutputWiring.ref_key)
          : null;
      }

      if (nodeId) {
        let filters;
        if (inputOrOutputWiring.ref_id_type === 'THINGNODE') {
          for (const nodeHash of Object.values(nodesHash)) {
            const nodeHashObj: SourceSinkNode = nodeHash as SourceSinkNode;
            if (nodeHashObj.metadataKey === inputOrOutputWiring.ref_key) {
              filters =
                (nodesHash[nodeHashObj.id] as SourceSinkNode)?.filters ?? [];
            }
          }
        } else {
          filters = (nodesHash[nodeId] as SourceSinkNode)?.filters ?? [];
        }
        if (filters) {
          textFilters = this.getTextFilters(filters, inputOrOutputWiring);
        }
      }

      const tmpInputWiring = inputOrOutputWiring as InputWiring;
      if (
        sourceType === 'INPUT_WIRING' &&
        Utils.isDefined(tmpInputWiring.filters)
      ) {
        manualValue = tmpInputWiring.filters.value ?? null;
        if (ioItem.type === IOTypeOption.OPTIONAL) {
          useDefaultValue = tmpInputWiring.use_default_value ?? true;
        } else {
          useDefaultValue = false;
        }
        if (useDefaultValue) {
          manualValue = ioItem.value ?? '';
        }
        if (Utils.isDefined(tmpInputWiring.filters.timestampFrom)) {
          // If both "From" and "To" timestamps are valid moment objects, it's a saved timestampRangePicker selection
          // else it's a saved timestampRangeQuery.
          if (
            moment(tmpInputWiring.filters.timestampFrom, true).isValid() &&
            moment(tmpInputWiring.filters.timestampTo, true).isValid()
          ) {
            timestampFrom = this.resetSecondsAndMilliseconds(
              moment(tmpInputWiring.filters.timestampFrom)
            );
            timestampTo = this.resetSecondsAndMilliseconds(
              moment(tmpInputWiring.filters.timestampTo)
            );
          } else {
            timestampRangeQuery = `${tmpInputWiring.filters.timestampFrom}\
${this._timestampRangeQueryDelimiter}${tmpInputWiring.filters.timestampTo}`;
            timestampRangePickerHidden = true;
          }
        } else {
          timestampFrom = this.resetSecondsAndMilliseconds(moment());
          timestampTo = this.resetSecondsAndMilliseconds(moment());
        }
        const node = Utils.isDefined(nodeId) ? nodesHash[nodeId] : null;
        if (
          AdapterHttpService.isSourceOrSinkNode(node) &&
          AdapterHttpService.isDateFilter(node.filters)
        ) {
          timestampMin = moment(node.filters.fromTimestamp.min);
          timestampMax = moment(node.filters.toTimestamp.max);
        }
      }
    } else {
      if (useDefaultValue) {
        manualValue = ioItem.value ?? '';
      }
    }
    const wiringUi: OptionalMembers<
      UiItemWiring,
      'nodeType' | 'refIdType' | 'adapterId'
    > = {
      ioItemName: ioItem.name,
      ioItemId: ioItem.id,
      rawValue: manualValue,
      nodeId,
      nodeName,
      displayName: null, // will be calculated from nodeName and metaDataKey. See @ _setInputOrOutputFormConfigurations function
      nodeType: inputOrOutputWiring ? inputOrOutputWiring.type : null,
      metaDataKey: inputOrOutputWiring?.ref_key ?? null,
      refIdType: inputOrOutputWiring ? inputOrOutputWiring.ref_id_type : null,
      ioType: ioItem.data_type,
      timestampRange: [timestampFrom, timestampTo],
      timestampRangeQuery,
      timestampRangeFilter: [timestampMin, timestampMax],
      timestampRangePickerHidden,
      adapterId,
      textFilters: this.formBuilder.array(
        textFilters.map((filter: TextFilter) =>
          this.getTextFilterFormGroup(filter)
        )
      ),
      type: ioItem.type ?? IOTypeOption.REQUIRED,
      defaultValue: ioItem.value ?? '',
      useDefaultValue
    };
    const formGroup = this.formBuilder.group({
      ...wiringUi,
      rawValue: this.formBuilder.control({
        value: manualValue,
        disabled: useDefaultValue
      }),
      adapterId: this.formBuilder.control({
        value: adapterId,
        disabled: useDefaultValue
      }),
      timestampRange: this.formBuilder.control({
        value: wiringUi.timestampRange,
        disabled:
          this._configService.app_config
            .enableDateRangeSelectionOnSeriesTypes === false
      }),
      timestampRangeQuery: this.formBuilder.control({
        value: wiringUi.timestampRangeQuery,
        disabled:
          this._configService.app_config
            .enableDateRangeSelectionOnSeriesTypes === false
      }),
      timestampRangeFilter: this.formBuilder.control(
        wiringUi.timestampRangeFilter
      )
    });

    this._setInputOrOutputFormConfigurations(
      formGroup,
      adapterId,
      ioItem,
      sourceType
    );

    return formGroup;
  }

  private _setInputOrOutputFormConfigurations(
    formGroup: FormGroup,
    adapterId: string | null,
    ioItem: IO,
    sourceType: SourceType
  ): void {
    if (
      Utils.isNullOrUndefined(adapterId) ||
      adapterId === 'drop' ||
      adapterId === 'plot'
    ) {
      this._getControlOrFail(formGroup, 'displayName').disable();
    }

    this._getControlOrFail(formGroup, 'displayName').setValidators(
      this.nodeIdValidation(formGroup)
    );
    if (sourceType === 'INPUT_WIRING') {
      this._getControlOrFail(formGroup, 'rawValue').setValidators(
        this.inputTypeCheckIfAny(ioItem.type, ioItem.data_type, formGroup)
      );

      if (ioItem.data_type === IOType.SERIES) {
        this._getControlOrFail(formGroup, 'timestampRange').setValidators(
          this.timestampRangeValidation(formGroup)
        );
        this._getControlOrFail(formGroup, 'timestampRangeQuery').setValidators(
          this.timestampRangeQueryValidation(formGroup)
        );
      }
    }

    const nodeNameControl = this._getControlOrFail(formGroup, 'nodeName');
    const metaDataKeyControl = this._getControlOrFail(formGroup, 'metaDataKey');
    const adapterIdControl = this._getControlOrFail(formGroup, 'adapterId');

    combineLatest([
      nodeNameControl.valueChanges.pipe(startWith(nodeNameControl.value)),
      metaDataKeyControl.valueChanges.pipe(startWith(metaDataKeyControl.value)),
      adapterIdControl.valueChanges.pipe(startWith(adapterIdControl.value))
    ]).subscribe(([nodeName, metaDataKey, currentAdapterId]) => {
      if (
        Utils.isNullOrUndefined(currentAdapterId) ||
        currentAdapterId === 'drop' ||
        currentAdapterId === 'plot'
      ) {
        return;
      }
      const displayName = metaDataKey ? metaDataKey : nodeName;
      this._getControlOrFail(formGroup, 'displayName').setValue(displayName);
    });

    this._getControlOrFail(formGroup, 'adapterId').valueChanges.subscribe(
      changedAdapterId => {
        this._getControlOrFail(formGroup, 'nodeId').reset();
        this._getControlOrFail(formGroup, 'nodeName').reset();
        this._getControlOrFail(formGroup, 'displayName').reset();
        this._getControlOrFail(formGroup, 'metaDataKey').reset();
        this._getControlOrFail(formGroup, 'timestampRangeQuery').reset();
        this._getControlOrFail(formGroup, 'timestampRangePickerHidden').reset(
          false
        );
        if (changedAdapterId === AdapterHttpService.MANUAL_INPUT_ADAPTER_ID) {
          this._getControlOrFail(formGroup, 'timestampRange').reset([
            null,
            null
          ]);
          const textFilters = this._getControlOrFail(
            formGroup,
            'textFilters'
          ) as FormArray;
          textFilters.controls.forEach(control => {
            for (const controlsKey in (control as FormGroup).controls) {
              if (
                controlsKey !== 'filterKey' &&
                controlsKey !== 'required' &&
                controlsKey !== 'name'
              ) {
                (control as FormGroup).get(controlsKey)?.reset();
              }
            }
          });
        } else if (changedAdapterId === 'drop' || changedAdapterId === 'plot') {
          this._getControlOrFail(formGroup, 'rawValue').reset();
          this._getControlOrFail(formGroup, 'timestampRange').reset([
            null,
            null
          ]);
          const textFilters = this._getControlOrFail(
            formGroup,
            'textFilters'
          ) as FormArray;
          textFilters.controls.forEach(control => {
            for (const controlsKey in (control as FormGroup).controls) {
              if (
                controlsKey !== 'filterKey' &&
                controlsKey !== 'required' &&
                controlsKey !== 'name'
              ) {
                (control as FormGroup).get(controlsKey)?.reset();
              }
            }
          });
        } else {
          this._getControlOrFail(formGroup, 'rawValue').reset();
          this._getControlOrFail(formGroup, 'timestampRange').setValue([
            this.resetSecondsAndMilliseconds(moment()),
            this.resetSecondsAndMilliseconds(moment())
          ]);
        }

        if (
          Utils.isNullOrUndefined(changedAdapterId) ||
          changedAdapterId === 'drop' ||
          changedAdapterId === 'plot'
        ) {
          this._getControlOrFail(formGroup, 'displayName').disable();
        } else {
          this._getControlOrFail(formGroup, 'displayName').enable();
        }
      }
    );

    this._getControlOrFail(formGroup, 'useDefaultValue').valueChanges.subscribe(
      valueChange => {
        const adapterListControl = this._getControlOrFail(
          formGroup,
          'adapterId'
        );
        const inputValueControl = this._getControlOrFail(formGroup, 'rawValue');

        this._getControlOrFail(formGroup, 'adapterId').reset(
          AdapterHttpService.MANUAL_INPUT_ADAPTER_ID
        );

        if (valueChange) {
          adapterListControl.disable();
          inputValueControl.setValue(
            this._getControlOrFail(formGroup, 'defaultValue').value
          );
          inputValueControl.disable();
        } else {
          adapterListControl.enable();
          inputValueControl.enable();
        }
      }
    );
  }

  private resetSecondsAndMilliseconds(date: Moment): Moment {
    date.set('second', 0);
    date.set('millisecond', 0);
    return date;
  }

  timestampRangeValidation(
    formGroup: FormGroup
  ): (control: AbstractControl) => ValidationErrors | null {
    return (control: AbstractControl): ValidationErrors | null => {
      let validationErrorOrNull: ValidationErrors | null = null;

      if (!this._getControlOrFail(formGroup, 'nodeId').value) {
        return validationErrorOrNull;
      }

      const [fromTimeRange, toTimeRange]: [Moment | null, Moment | null] =
        control.value;

      if (!fromTimeRange || !toTimeRange) {
        validationErrorOrNull = {
          noTimeRange: {
            value: control.value
          },
          message: 'time range is invalid'
        };
        return validationErrorOrNull;
      }

      if (isNaN(fromTimeRange.valueOf()) || isNaN(toTimeRange.valueOf())) {
        validationErrorOrNull = {
          noTimeRange: {
            value: control.value
          },
          message: 'time range is invalid'
        };
        return validationErrorOrNull;
      }

      return validationErrorOrNull;
    };
  }

  timestampRangeQueryValidation(
    formGroup: FormGroup
  ): (control: AbstractControl) => ValidationErrors | null {
    return (control: AbstractControl): ValidationErrors | null => {
      let validationErrorOrNull: ValidationErrors | null = null;

      if (!this._getControlOrFail(formGroup, 'nodeId').value) {
        return validationErrorOrNull;
      }

      const timestampRangeQuery: string | null = control.value;

      if (
        timestampRangeQuery !== null &&
        timestampRangeQuery.includes(this._timestampRangeQueryDelimiter)
      ) {
        const timestampRange = timestampRangeQuery.split(
          this._timestampRangeQueryDelimiter
        );
        if (timestampRange.length > 2) {
          validationErrorOrNull = {
            invalidDelimiter: {
              value: control.value
            },
            message: 'timestamp range query includes too many delimiters'
          };
          return validationErrorOrNull;
        }
      }

      if (timestampRangeQuery === '') {
        validationErrorOrNull = {
          noTimestampRangeQuery: {
            value: control.value
          },
          message: 'timestamp range query is invalid'
        };
        return validationErrorOrNull;
      }

      return validationErrorOrNull;
    };
  }

  nodeIdValidation(fromGroup: FormGroup): ValidatorFn {
    return (control: AbstractControl): ValidationErrors | null => {
      let validationErrorOrNull: ValidationErrors | null = null;
      // If no adapter is chosen, do not validate nodeId which is relevant on adapter is available.
      if (!this._parameterHasAdapter(fromGroup)) {
        return validationErrorOrNull;
      }

      const adapterId = fromGroup.get('adapterId')?.value;
      if (adapterId === 'drop' || adapterId === 'plot') {
        return null;
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

  ioItemTypeValidation(
    ioItemType: IOType,
    control: AbstractControl
  ): ValidationErrors | null {
    let validationErrorOrNull: ValidationErrors | null = null;
    const controlValue = control.value as string;

    switch (ioItemType) {
      case IOType.STRING:
        break;
      case IOType.BOOLEAN:
        const isBooleanValue =
          controlValue === 'True' || controlValue === 'False';
        if (!isBooleanValue) {
          validationErrorOrNull = {
            invalidType: {
              value: control.value
            },
            message: 'use True or False'
          };
        }
        break;
      case IOType.INT:
        if (!Utils.isInteger(controlValue)) {
          validationErrorOrNull = {
            invalidType: {
              value: control.value
            },
            message: 'not integer value'
          };
        }
        break;
      case IOType.FLOAT:
        if (!Utils.isFloat(controlValue)) {
          validationErrorOrNull = {
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
      case IOType.MULTITSFRAME:
        try {
          JSON.parse(controlValue);
          // eslint-disable-next-line @typescript-eslint/no-unused-vars
        } catch (error) {
          validationErrorOrNull = {
            invalidType: {
              value: control.value
            },
            message: 'invalid JSON'
          };
        }
        break;
      default:
    }

    return validationErrorOrNull;
  }

  /**
   * Validates input
   */
  inputTypeCheckIfAny(
    ioItemTypeOption: IOTypeOption,
    ioItemType: IOType,
    formGroup: FormGroup
  ): ValidatorFn {
    return (control: AbstractControl): ValidationErrors | null => {
      let validationErrorOrNull: ValidationErrors | null = null;
      const controlValue = control.value as string | null | undefined;

      // If a adapter is binned to the wiring, do not validate "raw value".
      if (this._parameterHasAdapter(formGroup)) {
        return validationErrorOrNull;
      }

      // Check if controlValue is null or undefined or a empty string.
      if (
        Utils.isNullOrUndefined(controlValue) ||
        Utils.string.isEmpty(controlValue)
      ) {
        validationErrorOrNull = {
          invalidType: {
            value: control.value
          },
          message: 'please enter a value'
        };
        return validationErrorOrNull;
      }

      // Check if ioItemType is null or undefined or controlValue is empty or undefined.
      if (
        Utils.isNullOrUndefined(ioItemType) ||
        Utils.string.isEmptyOrUndefined(controlValue)
      ) {
        validationErrorOrNull = {
          invalidType: {
            value: control.value
          },
          message: 'please enter a value'
        };
        return validationErrorOrNull;
      }

      const isControlValueOptionalAndNull =
        ioItemTypeOption === IOTypeOption.OPTIONAL && controlValue === 'null';

      if (!isControlValueOptionalAndNull) {
        validationErrorOrNull = this.ioItemTypeValidation(ioItemType, control);
      }

      return validationErrorOrNull;
    };
  }

  getTypeColor(type: string): string {
    return `var(--${type}-color)`;
  }

  isTimestampRangeType(type: IOType): boolean {
    return type === IOType.SERIES || type === IOType.MULTITSFRAME;
  }

  hasTextFilter(abstractControl: AbstractControl): boolean {
    return this.textFiltersFormArray(abstractControl).controls.length > 0;
  }

  textFiltersFormArray(abstractControl: AbstractControl): FormArray {
    return this._getControlOrFail(abstractControl, 'textFilters') as FormArray;
  }

  openAdapterTreeDialog(
    nodeSourceType: NodeSourceType,
    ioType: IOType,
    adapterId: string,
    sourceType: SourceType
  ): void {
    if (
      Utils.isNullOrUndefined(adapterId) ||
      adapterId === 'drop' ||
      adapterId === 'plot'
    ) {
      return;
    }

    const adapter = this._availableAdapters.find(
      adapters => adapters.id === adapterId
    );
    Utils.assert(adapter, `Adapter with id ${adapterId} is missing`);
    const data: AdapterTreeModalData = {
      nodeSourceType,
      initialDataTypeFilter: ioType,
      adapterUrl: adapter.url
    };
    const dialog = this.dialog.open<
      TreeNodeModalComponent,
      AdapterTreeModalData,
      never
    >(TreeNodeModalComponent, {
      width: '700px',
      data
    });

    dialog.componentInstance.nodeClick.subscribe(treeNodeItemClickEvent => {
      this.openWireAttributeToDataMenu(
        treeNodeItemClickEvent,
        adapter.id,
        sourceType
      );
      this.changeDetector.markForCheck();
    });

    dialog.componentInstance.nodeMetaDataClick
      .pipe(
        switchMap(nodeItemClickEvent => {
          const adapterUrl = nodeItemClickEvent.adapterUrl;
          Utils.assert(adapterUrl, 'Adapter url missing');
          let metaData$: Observable<MetaData[]> | undefined;
          switch (nodeItemClickEvent.nodeSourceType) {
            case 'SOURCE':
              metaData$ = this.adapterHttpService.getMetadataOfSource(
                adapterUrl,
                nodeItemClickEvent.node.id
              );
              break;
            case 'SINK':
              metaData$ = this.adapterHttpService.getMetadataOfSink(
                adapterUrl,
                nodeItemClickEvent.node.id
              );
              break;
            case 'THINGNODE':
              metaData$ = this.adapterHttpService.getMetadataOfThingNode(
                adapterUrl,
                nodeItemClickEvent.node.id
              );
              break;
            default:
              throw new Error(
                `${nodeItemClickEvent.nodeSourceType} is not a supported type`
              );
          }
          return combineLatest([metaData$, of(nodeItemClickEvent)]);
        })
      )
      .subscribe(([metaDataList, nodeClickEvent]) => {
        this._openMetaDataWiringModal(
          nodeClickEvent,
          metaDataList,
          sourceType,
          adapterId
        );
      });
  }

  private _openMetaDataWiringModal(
    nodeClickEvent: NodeClickEvent,
    metaDataList: MetaData[],
    sourceType: SourceType,
    adapterId: string
  ): void {
    // the node from tree
    const node = nodeClickEvent.node;
    let ioItems: UiItemWiring[];
    if (sourceType === 'INPUT_WIRING') {
      const formInputArray = this.inputOutputForm.get('inputs');
      Utils.assert(formInputArray instanceof FormArray);
      ioItems = formInputArray.getRawValue();
    } else if (sourceType === 'OUTPUT_WIRING') {
      const formOutputArray = this.inputOutputForm.get('outputs');
      Utils.assert(formOutputArray instanceof FormArray);
      ioItems = formOutputArray.getRawValue();
    } else {
      throw Error('unsupported source type');
    }

    // Only items are selectable, that have an adapterId.
    ioItems = ioItems.filter(ioItem => ioItem.adapterId);

    const dialogPositionAndMaxHeight =
      this.getDialogPositionAndMaxHeight(nodeClickEvent);

    const dialog = this.dialog.open<
      MetaDataWiringModalComponent,
      MetadataWiringModalData,
      never
    >(MetaDataWiringModalComponent, {
      width: 'fit-content',
      maxWidth: '600px',
      maxHeight: dialogPositionAndMaxHeight.maxHeight,
      disableClose: false,
      backdropClass: 'contextDropDown',
      position: dialogPositionAndMaxHeight.position,
      data: {
        nodeOrigin: node,
        IoItemWiring: ioItems,
        metaDataList
      }
    });

    dialog.componentInstance.metaDataWiringChange.subscribe(
      (metaDataWiringChangeEvent: MetaDataWiringChangeEvent) => {
        let inputOrOutputFormArray: FormArray;
        if (sourceType === 'INPUT_WIRING') {
          inputOrOutputFormArray = this.inputFormArray;
        } else if (sourceType === 'OUTPUT_WIRING') {
          inputOrOutputFormArray = this.outputFormArray;
        } else {
          throw Error('unsupported source type');
        }

        const foundIoItemControl = inputOrOutputFormArray.controls.find(
          control =>
            control.value.ioItemId === metaDataWiringChangeEvent.ioItemId
        );
        Utils.assert(
          foundIoItemControl,
          'meta data wiring dialog gets io items from this component as input data, so a match is normaly '
        );
        if (Utils.isNullOrUndefined(metaDataWiringChangeEvent.metaData)) {
          // eslint-disable-next-line @typescript-eslint/no-unused-expressions
          sourceType === 'INPUT_WIRING'
            ? this._clearInput(foundIoItemControl)
            : this._clearOutput(foundIoItemControl);
          this._getControlOrFail(foundIoItemControl, 'adapterId').setValue(
            adapterId
          );
          dialog.componentInstance._metaDataDialogData.IoItemWiring =
            inputOrOutputFormArray.getRawValue();
          return;
        }
        this._getControlOrFail(foundIoItemControl, 'adapterId').setValue(
          adapterId
        );
        this._getControlOrFail(foundIoItemControl, 'nodeName').setValue(
          node.name
        );
        this._getControlOrFail(foundIoItemControl, 'nodeId').setValue(node.id);
        this._getControlOrFail(foundIoItemControl, 'nodeType').setValue(
          `${DataStructureType.METADATA}(${metaDataWiringChangeEvent.metaData.dataType})`
        );

        this._getControlOrFail(foundIoItemControl, 'refIdType').setValue(
          nodeClickEvent.nodeSourceType
        );
        this._getControlOrFail(foundIoItemControl, 'metaDataKey').setValue(
          metaDataWiringChangeEvent.metaData.key
        );

        this._getControlOrFail(foundIoItemControl, 'rawValue').reset();
        dialog.componentInstance._metaDataDialogData.IoItemWiring =
          inputOrOutputFormArray.getRawValue();
        this.changeDetector.markForCheck();
      }
    );
  }

  openWireAttributeToDataMenu(
    nodeClickEvent: NodeClickEvent,
    adapterId: string,
    sourceType: SourceType
  ): void {
    // the node from tree
    const node = nodeClickEvent.node;
    let ioItems: UiItemWiring[];

    if (sourceType === 'INPUT_WIRING') {
      const formInputArray = this.inputOutputForm.get('inputs');
      Utils.assert(formInputArray instanceof FormArray);
      ioItems = formInputArray.getRawValue();
    } else if (sourceType === 'OUTPUT_WIRING') {
      const formOutputArray = this.inputOutputForm.get('outputs');
      Utils.assert(formOutputArray instanceof FormArray);
      ioItems = formOutputArray.getRawValue();
    } else {
      throw Error(`wiriing by ${sourceType} source type is not supported`);
    }

    // Only items are selectable, that have an adapterId.
    ioItems = ioItems.filter(ioItem => ioItem.adapterId);

    const dialogPositionAndMaxHeight =
      this.getDialogPositionAndMaxHeight(nodeClickEvent);

    const dialog = this.dialog.open<
      NodeWiringContextMenuComponent,
      ExecutionContextMenuData,
      never
    >(NodeWiringContextMenuComponent, {
      width: 'fit-content',
      maxWidth: '600px',
      maxHeight: dialogPositionAndMaxHeight.maxHeight,
      disableClose: false,
      backdropClass: 'contextDropDown',
      position: dialogPositionAndMaxHeight.position,
      data: {
        dataOrigin: node,
        IOItem: ioItems
      }
    });

    dialog.componentInstance.wiringChange.subscribe(
      (idAndChecked: WiringChangeEvent) => {
        let inputOrOutputControls: AbstractControl[];
        if (sourceType === 'INPUT_WIRING') {
          inputOrOutputControls = this.inputFormArray.controls;
        } else if (sourceType === 'OUTPUT_WIRING') {
          inputOrOutputControls = this.outputFormArray.controls;
        } else {
          throw Error(`wiring by ${sourceType} source type is not supported`);
        }

        const foundIoItemControl = inputOrOutputControls.find(
          control => control.value.ioItemId === idAndChecked.ioItemId
        );
        Utils.assert(
          foundIoItemControl,
          'wiring dialog gets io items from this component as input data, but the io item is not found.'
        );
        const realFilters = node.filters;
        if (AdapterHttpService.isDateFilter(realFilters)) {
          const timestampMin = moment(realFilters.fromTimestamp.min);
          const timestampMax = moment(realFilters.toTimestamp.max);
          this._getControlOrFail(
            foundIoItemControl,
            'timestampRangeFilter'
          ).setValue([timestampMin, timestampMax]);
        }

        const textFiltersArray = this._getControlOrFail(
          foundIoItemControl,
          'textFilters'
        ) as FormArray;
        textFiltersArray.clear();
        this.getTextFilters(realFilters).map((filter: TextFilter) => {
          textFiltersArray.push(this.getTextFilterFormGroup(filter));
        });

        this._getControlOrFail(foundIoItemControl, 'adapterId').setValue(
          idAndChecked.checked
            ? adapterId
            : AdapterHttpService.MANUAL_INPUT_ADAPTER_ID
        );
        this._getControlOrFail(foundIoItemControl, 'nodeName').setValue(
          idAndChecked.checked ? node.name : null
        );

        const nodeSourceType = nodeClickEvent.nodeSourceType;
        const nodeId =
          nodeSourceType === 'THINGNODE' ? node.thingNodeId : node.id;
        this._getControlOrFail(foundIoItemControl, 'nodeId').setValue(
          idAndChecked.checked ? nodeId : null
        );

        this._getControlOrFail(foundIoItemControl, 'nodeType').setValue(
          idAndChecked.checked ? node.type : null
        );
        this._getControlOrFail(foundIoItemControl, 'refIdType').setValue(
          idAndChecked.checked ? nodeSourceType : null
        );

        this._getControlOrFail(foundIoItemControl, 'metaDataKey').setValue(
          nodeSourceType === 'THINGNODE' && idAndChecked.checked
            ? node.metadataKey
            : null
        );

        this._getControlOrFail(foundIoItemControl, 'rawValue').reset();
        this.changeDetector.markForCheck();
      }
    );
  }

  onCancel(): void {
    this.cancelDialogClick.next();
  }

  onOk(): void {
    this.inputFormArray.controls.map((inputControl: AbstractControl) => {
      Utils.assert(
        inputControl instanceof FormGroup,
        'Form schema is flawed, formGroup after formArray not found.'
      );
      const uiWiring: UiItemWiring = inputControl.getRawValue() ?? null;
      const timestampRangePickerHidden = uiWiring.timestampRangePickerHidden;

      if (timestampRangePickerHidden) {
        this._getControlOrFail(inputControl, 'timestampRange').reset([
          this.resetSecondsAndMilliseconds(moment()),
          this.resetSecondsAndMilliseconds(moment())
        ]);
      } else {
        this._getControlOrFail(inputControl, 'timestampRangeQuery').reset();
      }
    });

    this.inputFormArray.markAllAsTouched();
    this.outputFormArray.markAllAsTouched();
    if (this.inputFormArray.invalid || this.outputFormArray.invalid) {
      return;
    }

    const reassembledWorkflowWiring: TestWiring = {
      input_wirings: [],
      output_wirings: []
    };

    const inputWirings: InputWiring[] = this.inputFormArray.controls.map(
      // eslint-disable-next-line complexity
      (inputControl: AbstractControl) => {
        Utils.assert(
          inputControl instanceof FormGroup,
          'Form schema is flawed, formGroup after formArray not found.'
        );
        const uiWiring: UiItemWiring = inputControl.getRawValue() ?? null;
        let filters: InputFilters = {};

        if (Utils.isDefined(uiWiring.rawValue)) {
          filters.value = uiWiring.rawValue;
        }
        // Apply timestamp only for series and for non manual selection.
        if (
          (uiWiring.ioType === IOType.SERIES ||
            uiWiring.ioType === IOType.MULTITSFRAME) &&
          Utils.isNullOrUndefined(uiWiring.rawValue)
        ) {
          const timestampRange = uiWiring.timestampRange;
          const timestampRangeQuery = uiWiring.timestampRangeQuery;
          const timestampRangePickerHidden =
            uiWiring.timestampRangePickerHidden;

          if (timestampRangePickerHidden) {
            Utils.assert(
              timestampRangeQuery,
              'For series and non manual selection time range selection are required'
            );
            filters = {
              timestampFrom:
                this._splitTimestampRangeQuery(timestampRangeQuery)[0] ??
                undefined,
              timestampTo:
                this._splitTimestampRangeQuery(timestampRangeQuery)[1] ??
                undefined
            };
          } else {
            Utils.assert(
              timestampRange,
              'For series and non manual selection time range selection are required'
            );
            filters = {
              timestampFrom:
                this.dateFormatter.transform(
                  timestampRange[0]?.valueOf(),
                  // eslint-disable-next-line @stylistic/quotes
                  "yyyy-MM-dd'T'HH:mm:ss.SSSSSSSSS'Z'",
                  '+0000'
                ) ?? undefined,
              timestampTo:
                this.dateFormatter.transform(
                  timestampRange[1]?.valueOf(),
                  // eslint-disable-next-line @stylistic/quotes
                  "yyyy-MM-dd'T'HH:mm:ss.SSSSSSSSS'Z'",
                  '+0000'
                ) ?? undefined
            };
          }
        }

        const textFilters = uiWiring.textFilters as Array<any>;

        for (const textFilter of textFilters) {
          const filterKey = textFilter.filterKey;
          const filterValue = textFilter[`value_${filterKey}`];
          filters[filterKey] = filterValue ?? '';
        }

        return {
          workflow_input_name: uiWiring.ioItemName,
          adapter_id: uiWiring.adapterId,
          ref_id: uiWiring.nodeId ?? undefined,
          ref_id_type: uiWiring.refIdType ?? undefined,
          ref_key: uiWiring.metaDataKey ?? undefined,
          type: uiWiring.nodeType ?? undefined,
          filters: filters ?? undefined,
          use_default_value: uiWiring.useDefaultValue ?? false
        };
      }
    );

    const outputWirings: OutputWiring[] = this.outputFormArray.controls
      .filter(control => {
        Utils.assert(
          control instanceof FormGroup,
          'Form schema is flawed, formGroup after formArray not found'
        );
        const rawValue: UiItemWiring = control.getRawValue();
        return Utils.isDefined(rawValue.adapterId);
      })
      .map(control => {
        Utils.assert(
          control instanceof FormGroup,
          'Form schema is flawed, formGroup after formArray not found'
        );
        const uiWiring: UiItemWiring = control.getRawValue();
        const textFilters = uiWiring.textFilters as Array<any>;
        const filters: InputFilters = {};

        for (const textFilter of textFilters) {
          const filterKey = textFilter.filterKey;
          const filterValue = textFilter[`value_${filterKey}`];
          filters[filterKey] = filterValue ?? '';
        }
        return {
          workflow_output_name: uiWiring.ioItemName,
          adapter_id: uiWiring.adapterId,
          ref_id: uiWiring.nodeId ?? undefined,
          ref_id_type: uiWiring.refIdType ?? undefined,
          ref_key: uiWiring.metaDataKey ?? undefined,
          type: uiWiring.nodeType ?? undefined,
          filters: filters ?? undefined
        };
      });

    reassembledWorkflowWiring.input_wirings = inputWirings;
    reassembledWorkflowWiring.output_wirings = outputWirings;

    this.confirmClick.emit({
      id: this.wiringItem.id,
      test_wiring: reassembledWorkflowWiring
    });
  }

  openJsonEditorModal(inputControl: AbstractControl): void {
    const rawValue =
      this._getControlOrFail(inputControl, 'rawValue').value ?? '';
    const ioType: IOType = this._getControlOrFail(inputControl, 'ioType').value;
    const exampleValue = JSON.stringify(
      this._getExampleValueForIoType(ioType),
      null,
      4
    );
    const data: JsonEditorModalData = {
      value: rawValue,
      exampleValue,
      dataType: ioType,
      actionOk: 'Save',
      actionCancel: 'Cancel',
      title: `Json input for ${
        this._getControlOrFail(inputControl, 'ioItemName').value
      }`
    };
    const dialog = this.dialog.open<
      JsonEditorComponent,
      JsonEditorModalData,
      string
    >(JsonEditorComponent, {
      width: '600px',
      data
    });

    dialog.afterClosed().subscribe(json => {
      this._getControlOrFail(inputControl, 'rawValue').setValue(json);
    });
  }

  uploadJsonForAllInputs(jSONInput: HTMLInputElement): void {
    jSONInput.click();
  }

  downloadJsonSchema(): void {
    const fileName = `jsonschema_${this.wiringItem.name}_${this.wiringItem.version_tag}.json`;
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
  private _generateJSONSchema(withExampleData: boolean = false): {
    [i: string]: any;
  } {
    const generatedJsonSchema: {
      [key: string]: any;
    } = {};

    this.inputFormArray.controls.forEach(control => {
      const inputName = this._getControlOrFail(control, 'ioItemName')
        .value as string;
      const ioType = this._getControlOrFail(control, 'ioType').value as IOType;
      if (withExampleData) {
        generatedJsonSchema[inputName] = this._getExampleValueForIoType(ioType);
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
   * @param ioType dataType
   */
  private _getExampleValueForIoType(ioType: IOType): any {
    let exampleValue = null;
    switch (ioType) {
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
      case IOType.MULTITSFRAME:
        exampleValue = {
          value: [1.0, 1.2, 0.5],
          metric: ['a', 'b', 'c'],
          timestamp: [
            '2019-08-01T15:45:36.000Z',
            '2019-08-01T15:48:36.000Z',
            '2019-08-01T15:42:36.000Z'
          ]
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

  private getTextFilters(
    filters: any,
    inputOrOutputWiring?: InputOrOutputWiring
  ): TextFilter[] {
    const textFilters: TextFilter[] = [];
    if (filters) {
      for (const [key, obj] of Object.entries(filters)) {
        const filter: FreeTextFilter = obj as FreeTextFilter;
        if (filter.type === 'free_text') {
          let filterValue = '';
          if (inputOrOutputWiring && 'filters' in inputOrOutputWiring) {
            filterValue = (inputOrOutputWiring.filters as any)[key] ?? '';
          }
          // A default_value for a filter, can be send via selected adapter source.
          if (
            filterValue === '' &&
            !Utils.isNullOrUndefined(filter.default_value)
          ) {
            filterValue = filter.default_value;
          }
          textFilters.push({
            ...filter,
            key,
            value: filterValue
          });
        }
      }
    }
    return textFilters;
  }

  private getTextFilterFormGroup(filter: TextFilter): FormGroup {
    return this.formBuilder.group({
      filterKey: filter.key,
      [`value_${filter.key}`]: this.formBuilder.control(filter.value ?? ''),
      required: filter.required,
      name: filter.name ? filter.name : filter.key
    });
  }

  /**
   * The dialog would normally overflow the bottom or top screen with large lists inside,
   * if the maxHeight is set statically.
   * To prevent it from happening we render it above or below the cursor and calc his maxHeight
   * from the current cursor position onClick, to the bottom or top of the screen, minus some padding.
   */
  private getDialogPositionAndMaxHeight(
    nodeClickEvent: NodeClickEvent
  ): DialogPositionAndMaxHeight {
    const clickPositionX = nodeClickEvent.event.clientX;
    const clickPositionY = nodeClickEvent.event.clientY;
    const padding = 10;
    const maxHeightDefault = 500;

    let dialogPositionAndMaxHeight: DialogPositionAndMaxHeight = {
      position: {
        top: '250px',
        left: `${clickPositionX}px`
      },
      maxHeight: `${maxHeightDefault}px`
    };

    if (nodeClickEvent.event.view) {
      const windowHeight = nodeClickEvent.event.view?.innerHeight;
      const windowHeightDivided = windowHeight / 2;
      if (clickPositionY <= windowHeightDivided) {
        dialogPositionAndMaxHeight = {
          position: {
            top: `${clickPositionY}px`,
            left: `${clickPositionX}px`
          },
          maxHeight: `${windowHeight - clickPositionY - padding}px`
        };
      } else {
        dialogPositionAndMaxHeight = {
          position: {
            bottom: `${windowHeight - clickPositionY}px`,
            left: `${clickPositionX}px`
          },
          maxHeight: `${clickPositionY - padding}px`
        };
      }
    }

    return dialogPositionAndMaxHeight;
  }

  private _splitTimestampRangeQuery(timestampRangeQuery: string): string[] {
    let timestampRange: string[] = [];

    if (timestampRangeQuery.includes(this._timestampRangeQueryDelimiter)) {
      timestampRange = timestampRangeQuery.split(
        this._timestampRangeQueryDelimiter
      );
    } else {
      timestampRange.push(timestampRangeQuery, '');
    }
    return timestampRange;
  }

  _changeTimestampRangePicker(inputControl: AbstractControl): boolean {
    const timestampRangePickerHidden = !this._getControlOrFail(
      inputControl,
      'timestampRangePickerHidden'
    ).value;
    this._getControlOrFail(inputControl, 'timestampRangePickerHidden').setValue(
      timestampRangePickerHidden
    );

    return timestampRangePickerHidden;
  }

  _parameterHasAdapter(abstractControl: AbstractControl): boolean {
    const adapterId = abstractControl.get('adapterId');
    Utils.assert(adapterId, 'missing formGroup attribute "adapterId"');
    if (Utils.isNullOrUndefined(adapterId.value)) {
      return false;
    }
    return (
      adapterId.value !== AdapterHttpService.MANUAL_INPUT_ADAPTER_ID &&
      adapterId.value !== 'drop' &&
      adapterId.value !== 'plot'
    );
  }

  _isAdapterAvailable(): boolean {
    return this._availableAdapters.length !== 0;
  }

  _adapterListForInputParameter(): (Adapter | Omit<Adapter, 'url'>)[] {
    const inputAdapters = this._availableAdapters.filter(
      availableAdapters =>
        availableAdapters.id !== 'drop' && availableAdapters.id !== 'plot'
    );

    if (
      Utils.isNullOrUndefined(
        this._configService.app_config.allowManualWiring
      ) ||
      this._configService.app_config.allowManualWiring === false
    ) {
      return inputAdapters;
    }
    return [AdapterHttpService.MANUAL_INPUT_ADAPTER, ...inputAdapters];
  }

  triggerForAllInputs(jSONInput: HTMLInputElement): void {
    const uploadedFile = jSONInput.files?.item(0);
    const fileReader = new FileReader();

    fileReader.onload = () => {
      const textJson = fileReader.result as string;
      try {
        const importedJson = JSON.parse(textJson);
        this.inputFormArray.controls.forEach(inputControl => {
          const foundAttribute =
            importedJson[
              this._getControlOrFail(inputControl, 'ioItemName').value
            ];
          if (Utils.isDefined(foundAttribute)) {
            this._getControlOrFail(inputControl, 'adapterId').setValue(
              AdapterHttpService.MANUAL_INPUT_ADAPTER_ID
            );
            this._getControlOrFail(inputControl, 'nodeId').reset(null);
            this._getControlOrFail(inputControl, 'rawValue').setValue(
              typeof foundAttribute === 'string'
                ? foundAttribute
                : JSON.stringify(foundAttribute, null, 4)
            );
          } else {
            // TODO display a warning, because in importedJson are missing input fields.
          }

          this._getControlOrFail(inputControl, 'rawValue').markAllAsTouched();
          this.changeDetector.markForCheck();
        });
        this.jsonImportErrorStatus.next('');
        // eslint-disable-next-line @typescript-eslint/no-unused-vars
      } catch (error) {
        this.jsonImportErrorStatus.next('JSON is malformed.');
        this.changeDetector.markForCheck();
      }
    };

    if (Utils.isDefined(uploadedFile)) {
      fileReader.readAsText(uploadedFile);
    }

    // remove uploaded data from input element
    // otherwise files with same name will don´t uploaded again.
    jSONInput.value = '';
  }

  isJsonType(ioType: IOType): boolean {
    let isJsonType = false;
    if (
      ioType === IOType.SERIES ||
      ioType === IOType.DATAFRAME ||
      ioType === IOType.MULTITSFRAME ||
      ioType === IOType.ANY
    ) {
      isJsonType = true;
    }

    return isJsonType;
  }

  private _openSourceSinkOrThingNodeInfoMissingDialog(error?: any): void {
    this.dialog.open(WarningDialogComponent, {
      data: { error },
      width: '50vw'
    });
  }

  _clearOutput(outputControl: AbstractControl): void {
    this._getControlOrFail(outputControl, 'refIdType').reset(null);
    this._getControlOrFail(outputControl, 'metaDataKey').reset(null);
    this._getControlOrFail(outputControl, 'nodeId').reset(null);
    this._getControlOrFail(outputControl, 'nodeName').reset(null);
    this._getControlOrFail(outputControl, 'nodeType').reset(null);
    this._getControlOrFail(outputControl, 'adapterId').reset(null);
    (this._getControlOrFail(outputControl, 'textFilters') as FormArray).clear();
  }

  _clearInput(inputControl: AbstractControl): void {
    this._getControlOrFail(inputControl, 'adapterId').reset(
      AdapterHttpService.MANUAL_INPUT_ADAPTER_ID
    );
    this._getControlOrFail(inputControl, 'refIdType').reset(null);
    this._getControlOrFail(inputControl, 'rawValue').reset(null);
    this._getControlOrFail(inputControl, 'metaDataKey').reset(null);
    this._getControlOrFail(inputControl, 'nodeId').reset(null);
    this._getControlOrFail(inputControl, 'nodeName').reset(null);
    this._getControlOrFail(inputControl, 'nodeType').reset(null);
    this._getControlOrFail(inputControl, 'useDefaultValue').reset(false);
    this._getControlOrFail(inputControl, 'timestampRange').reset([null, null]);
    this._getControlOrFail(inputControl, 'timestampRangeQuery').reset(null);
    this._getControlOrFail(inputControl, 'timestampRangePickerHidden').reset(
      false
    );
    (this._getControlOrFail(inputControl, 'textFilters') as FormArray).clear();
  }

  _stringValueOfFormControl(control: AbstractControl): string {
    const value = control.value;
    if (Utils.isNullOrUndefined(value)) {
      return '';
    }

    return String(value);
  }

  _isDefaultValue(abstractControl: AbstractControl): boolean {
    return (
      this._getControlOrFail(abstractControl, 'type').value ===
      IOTypeOption.OPTIONAL
    );
  }
}
