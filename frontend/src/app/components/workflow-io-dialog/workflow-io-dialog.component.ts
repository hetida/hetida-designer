import {
  AfterViewInit,
  ChangeDetectionStrategy,
  ChangeDetectorRef,
  Component,
  Inject
} from '@angular/core';
import {
  AbstractControl,
  FormArray,
  FormBuilder,
  FormControl,
  FormGroup,
  Validators
} from '@angular/forms';
import {
  MAT_DIALOG_DATA,
  MatDialog,
  MatDialogRef
} from '@angular/material/dialog';
import { IO, JsonEditorComponent, JsonEditorModalData } from 'hd-wiring';
import {
  createReadOnlyConfig,
  FlowchartConfiguration,
  IOType,
  IOTypeOption,
  SVGManipulatorConfiguration
} from 'hetida-flowchart';
import { FlowchartConverterService } from 'src/app/service/type-converter/flowchart-converter.service';
import {
  BooleanValidator,
  FloatValidator,
  IntegerValidator
} from 'src/app/validation/basic-type-validators';
import { PythonIdentifierValidator } from 'src/app/validation/python-identifier-validator';
import { PythonKeywordBlacklistValidator } from 'src/app/validation/python-keyword-validator';
import { UniqueValueValidator } from 'src/app/validation/unique-value-validator';
import { WorkflowTransformation } from '../../model/transformation';
import { Operator } from 'src/app/model/operator';
import { Connector } from 'src/app/model/connector';
import { Constant } from 'src/app/model/constant';
import { IOConnector } from 'src/app/model/io-connector';

export interface WorkflowIODialogData {
  workflowTransformation: WorkflowTransformation;
  editMode: boolean;
  actionOk: string;
  actionCancel: string;
}

export class WorkflowIODefinition {
  operator: string;
  connector: string;
  type: string;
  isConstant: boolean;
  name: string;
  constant: string;
  id: string;
  typeOption: IOTypeOption;
  value?: string;

  constructor(
    workflowIO: IO | Constant,
    operator: Operator,
    connector: Connector
  ) {
    this.operator = operator.name;
    this.connector = connector.name;
    this.type = workflowIO.data_type;
    this.name = workflowIO.name;
    this.typeOption = workflowIO.type ?? ('FIXED' as IOTypeOption);
    this.value = workflowIO.value ?? '';
    if (ioIsConstant(workflowIO)) {
      this.isConstant = true;
      this.constant = workflowIO.value ?? '';
    } else {
      this.isConstant = false;
      this.constant = '';
    }
    this.id = workflowIO.id;
  }
}

function ioIsConstant(io: IO | Constant): io is Constant {
  let ioConstant: boolean;
  if ('value' in io) {
    ioConstant = !('type' in io && io.type !== ('FIXED' as IOTypeOption));
  } else {
    ioConstant = false;
  }
  return ioConstant;
}

@Component({
  templateUrl: 'workflow-io-dialog.component.html',
  styleUrls: ['./workflow-io-dialog.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush
})
export class WorkflowIODialogComponent implements AfterViewInit {
  ioItemForm: FormGroup;

  readonly _ioTypeOptions = Object.keys(IOTypeOption);

  get ioItemInputsArray(): FormArray {
    return this.ioItemForm.get('inputs') as FormArray;
  }

  get ioItemOutputsArray(): FormArray {
    return this.ioItemForm.get('outputs') as FormArray;
  }

  preview: FlowchartConfiguration = {
    id: '',
    components: [],
    io: [],
    links: []
  };

  svgConfiguration: SVGManipulatorConfiguration;

  constructor(
    private readonly dialogRef: MatDialogRef<WorkflowIODialogComponent>,
    @Inject(MAT_DIALOG_DATA) public data: WorkflowIODialogData,
    private readonly flowchartConverter: FlowchartConverterService,
    private readonly formBuilder: FormBuilder,
    private readonly changeDetectorRef: ChangeDetectorRef,
    private readonly dialog: MatDialog
  ) {
    this.svgConfiguration = createReadOnlyConfig(
      new SVGManipulatorConfiguration()
    );
    this.svgConfiguration.allowPanning = false;
    this.svgConfiguration.allowZooming = false;
    this.svgConfiguration.showContextMenu = false;

    this.setupFormControl();
    // Extra value for IOTypeOption that is not defined in ENUM,
    // because is only needed in the Workflow dialog
    this._ioTypeOptions.push('FIXED');
  }

  ngAfterViewInit(): void {
    this.createPreview();
  }

  get valid(): boolean {
    return this.ioItemForm.valid;
  }

  getTypeColor(type: string): string {
    return `var(--${type}-color)`;
  }

  getIcon(ioItem: AbstractControl): string {
    switch (ioItem.get('typeOption').value) {
      case IOTypeOption.REQUIRED: {
        return 'lens';
      }
      case IOTypeOption.OPTIONAL: {
        return 'radio_button_checked';
      }
      default: {
        return 'panorama_fish_eye';
      }
    }
  }

  private setupFormControl(): void {
    const workflowTransformation: WorkflowTransformation =
      this.data.workflowTransformation;
    const inputData: WorkflowIODefinition[] = [];
    const outputData: WorkflowIODefinition[] = [];

    for (const input of workflowTransformation.content.inputs) {
      this.generateWorkflowIODefinition(
        input,
        workflowTransformation,
        inputData
      );
    }

    for (const constant of workflowTransformation.content.constants) {
      this.generateWorkflowIODefinition(
        constant,
        workflowTransformation,
        inputData
      );
    }

    for (const output of workflowTransformation.content.outputs) {
      this.generateWorkflowIODefinition(
        output,
        workflowTransformation,
        outputData
      );
    }
    const inputIOControlGroup = inputData.map(data =>
      this._createFormGroup(data)
    );
    const outputIOControlGroup = outputData.map(data =>
      this._createFormGroup(data)
    );

    this.ioItemForm = this.formBuilder.group({
      inputs: this.formBuilder.array(
        inputIOControlGroup,
        inputIOControlGroup.length > 0 ? UniqueValueValidator('name') : null
      ),
      outputs: this.formBuilder.array(
        outputIOControlGroup,
        outputIOControlGroup.length > 0 ? UniqueValueValidator('name') : null
      )
    });
  }

  private _createFormGroup(data: WorkflowIODefinition): FormGroup {
    const constantControl = this.createConstantControl(data);
    const nameControl = this.createNameControl(data);
    const valueControl = this.createValueControl(data);
    const inputTypeControl = this.createInputTypeControl(data);

    const form = this.formBuilder.group({
      operator: data.operator,
      connector: data.connector,
      type: data.type,
      isConstant: data.isConstant,
      id: data.id,
      constant: constantControl,
      name: nameControl,
      typeOption: inputTypeControl,
      value: valueControl
    });

    nameControl.valueChanges.subscribe(() => {
      this.updateWorkflowIO(form.getRawValue());
    });

    constantControl.valueChanges.subscribe(() => {
      this.updateWorkflowIO(form.getRawValue());
    });

    valueControl.valueChanges.subscribe(() => {
      this.updateWorkflowIO(form.getRawValue());
    });

    inputTypeControl.valueChanges.subscribe(() => {
      this.updateWorkflowIO(form.getRawValue());
    });

    return form;
  }

  private generateWorkflowIODefinition(
    workflowContentIO: IOConnector | Constant,
    workflowTransformation: WorkflowTransformation,
    dataArray: WorkflowIODefinition[]
  ): void {
    const operator = workflowTransformation.content.operators.find(
      op => op.id === workflowContentIO.operator_id
    );
    if (operator === undefined) {
      throw new Error(
        `Could not find operator with id '${workflowContentIO.operator_id}'`
      );
    }
    let isOutput = false;
    let connector = operator.inputs.find(
      io => io.id === workflowContentIO.connector_id
    );
    if (connector === undefined) {
      connector = operator.outputs.find(
        io => io.id === workflowContentIO.connector_id
      );
      if (connector) {
        isOutput = true;
      }
    }
    if (connector === undefined) {
      throw new Error(
        `Could not find connector with id '${workflowContentIO.connector_id}'`
      );
    }
    const data = new WorkflowIODefinition(
      workflowContentIO,
      operator,
      connector
    );
    if (isOutput || connector.exposed) {
      dataArray.push(data);
    }
  }

  _isDefaultParameter(ioItem: AbstractControl): boolean {
    return ioItem.get('typeOption').value === IOTypeOption.OPTIONAL;
  }

  _ioTypeOptionChanged(event: IOTypeOption, ioItem: AbstractControl) {
    const isConstantControl = ioItem.get('isConstant');
    ioItem.patchValue({
      typeOption: event
    });
    isConstantControl.setValue(
      event !== IOTypeOption.OPTIONAL && event !== IOTypeOption.REQUIRED
    );
    ioItem.patchValue({
      value: null
    });
    this.toggleConstant(ioItem);
  }

  toggleConstant(workflowIODefinitionForm: AbstractControl): void {
    const isConstant = workflowIODefinitionForm.get('isConstant').value;
    const constantControl = workflowIODefinitionForm.get('constant');
    const nameControl = workflowIODefinitionForm.get('name');

    const rawValue = (
      workflowIODefinitionForm as FormGroup
    ).getRawValue() as WorkflowIODefinition;

    if (isConstant) {
      nameControl.reset('');
      nameControl.clearValidators();
      nameControl.updateValueAndValidity();
      constantControl.setValidators(this.getValidators(rawValue));
    } else {
      constantControl.reset('');
      constantControl.clearValidators();
      constantControl.updateValueAndValidity();
      nameControl.setValidators(this.getValidators(rawValue));
    }

    this.updateWorkflowIO(rawValue);
  }

  resetInputOrOutput(inputOrOutputControl: AbstractControl) {
    inputOrOutputControl.get('isConstant').reset(false);
    inputOrOutputControl.get('constant').reset('');
    inputOrOutputControl.get('constant').clearValidators();
    inputOrOutputControl.get('constant').updateValueAndValidity();
    inputOrOutputControl.get('name').reset('');
    inputOrOutputControl.get('typeOption').reset(IOTypeOption.REQUIRED);
    inputOrOutputControl.get('value').reset('');
    const rawValue = (inputOrOutputControl as FormGroup).getRawValue();
    inputOrOutputControl
      .get('name')
      .setValidators(this.getValidators(rawValue));
    inputOrOutputControl.get('name').updateValueAndValidity();
    this.updateWorkflowIO(rawValue);
    this.changeDetectorRef.detectChanges();
  }

  showEditorIcon(inputControl: AbstractControl): boolean {
    const ioType = inputControl.get('type').value as IOType;
    return (
      ioType === IOType.SERIES ||
      ioType === IOType.DATAFRAME ||
      ioType === IOType.ANY
    );
  }

  openJsonEditor(inputControl: AbstractControl) {
    const dialogRef = this.dialog.open<
      JsonEditorComponent,
      JsonEditorModalData,
      string
    >(JsonEditorComponent, {
      minHeight: '600px',
      width: '600px',
      data: {
        value: inputControl.get('constant').value,
        actionOk: 'Save',
        actionCancel: 'Cancel',
        dataType: inputControl.get('type').value
      }
    });

    dialogRef.afterClosed().subscribe((result: string) => {
      inputControl.get('constant').setValue(result);
    });
  }

  private createConstantControl(data: WorkflowIODefinition): FormControl {
    return this.formBuilder.control(
      {
        value: data.constant,
        disabled: !this.data.editMode
      },
      data.isConstant ? this.getValidators(data) : null
    );
  }

  private createNameControl(data: WorkflowIODefinition): FormControl {
    return this.formBuilder.control(
      {
        value: data.name,
        disabled: !this.data.editMode
      },
      !data.isConstant ? this.getValidators(data) : null
    );
  }

  private createValueControl(data: WorkflowIODefinition): FormControl {
    return this.formBuilder.control({
      value: data.value,
      disabled: !this.data.editMode
    });
  }

  private createInputTypeControl(data: WorkflowIODefinition): FormControl {
    return this.formBuilder.control({
      value: data.typeOption,
      disabled: !this.data.editMode
    });
  }

  private getValidators(data: WorkflowIODefinition) {
    if (data.isConstant) {
      switch (data.type) {
        case 'FLOAT':
          return [FloatValidator(), Validators.required];
        case 'INT':
          return [IntegerValidator(), Validators.required];
        case 'BOOLEAN':
          return [BooleanValidator(), Validators.required];
        default:
          return Validators.required;
      }
    } else {
      return [
        Validators.maxLength(60),
        PythonIdentifierValidator(true),
        PythonKeywordBlacklistValidator()
      ];
    }
  }

  private updateWorkflowIO(data: WorkflowIODefinition): void {
    // TODO do not mutate the dialog data, take a copy from form control
    const foundInput = this.data.workflowTransformation.content.inputs.find(
      (ref: IOConnector) => ref.id === data.id
    );
    const foundConstant =
      this.data.workflowTransformation.content.constants.find(
        ref => ref.id === data.id
      );
    const foundOutput: IOConnector | undefined =
      this.data.workflowTransformation.content.outputs.find(
        (ref: IOConnector) => ref.id === data.id
      );
    if (foundConstant && data.isConstant) {
      foundConstant.value = data.constant;
    } else if (foundInput && !data.isConstant) {
      foundInput.name = data.name;
      foundInput.type = data.typeOption;
      if (data.typeOption === IOTypeOption.OPTIONAL) {
        foundInput.value = data.value;
      }
      if (data.typeOption === IOTypeOption.REQUIRED) {
        foundInput.value = null;
      }
      this.data.workflowTransformation.io_interface.inputs.forEach(input => {
        if (input.id === foundInput.id) {
          input.name = foundInput.name;
        }
      });
    } else if (foundInput && data.isConstant) {
      // move data from inputs to constants
      this.data.workflowTransformation.content.inputs =
        this.data.workflowTransformation.content.inputs.filter(
          input => input.id !== foundInput.id
        );
      const newConstant: Constant = {
        ...foundInput,
        name: null,
        value: data.constant
      };
      this.data.workflowTransformation.content.constants.push(newConstant);
    } else if (foundConstant && !data.isConstant) {
      // move data from constants to inputs
      this.data.workflowTransformation.content.constants =
        this.data.workflowTransformation.content.constants.filter(
          constant => constant.id !== foundConstant.id
        );
      const newInput: IOConnector = {
        ...foundConstant,
        name: data.name,
        type: data.typeOption,
        position: {
          x: 0,
          y: 0
        }
      };
      this.data.workflowTransformation.content.inputs.push(newInput);
    } else if (foundOutput) {
      foundOutput.name = data.name;
    } else {
      throw new Error(`Could not find IO with id '${data.id}'`);
    }
    this.createPreview();
  }

  onOk(): void {
    if (this.data.editMode === false) {
      this.dialogRef.close(false);
    } else {
      this.dialogRef.close({
        constants: this.data.workflowTransformation.content.constants,
        inputs: this.data.workflowTransformation.content.inputs,
        outputs: this.data.workflowTransformation.content.outputs
      });
    }
  }

  onCancel(): void {
    this.dialogRef.close(false);
  }

  private createPreview(): void {
    if (this.data.workflowTransformation === undefined) {
      return;
    }
    this.preview = this.flowchartConverter.convertComponentToFlowchart(
      this.data.workflowTransformation
    );
  }
}
