import {
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
import {
  Transformation,
  WorkflowTransformation
} from '../../model/new-api/transformation';
import { Operator } from 'src/app/model/new-api/operator';
import { Connector } from 'src/app/model/new-api/connector';
import { Constant } from 'src/app/model/new-api/constant';
import { IOConnector } from 'src/app/model/new-api/io-connector';

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

  constructor(
    workflowIO: IO,
    operator: Operator,
    connector: Connector,
    constant: Constant
  ) {
    this.operator = operator.name;
    this.connector = connector.name;
    this.type = workflowIO.data_type;
    this.isConstant = constant.value !== undefined ? true : false;
    this.name = workflowIO.name;
    if (constant === undefined || constant.value === undefined) {
      this.constant = '';
    } else {
      this.constant = constant.value;
    }
    this.id = workflowIO.id;
  }
}

@Component({
  templateUrl: 'workflow-io-dialog.component.html',
  styleUrls: ['./workflow-io-dialog.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush
})
export class WorkflowIODialogComponent {
  ioItemForm: FormGroup;

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

    this.createPreview();
    this.setupFormControl();
  }

  get valid(): boolean {
    return this.ioItemForm.valid;
  }

  getTypeColor(type: string): string {
    return `var(--${type}-color)`;
  }

  private setupFormControl(): void {
    const workflowTransformation: WorkflowTransformation = this.data
      .workflowTransformation;
    const inputData: WorkflowIODefinition[] = [];
    const outputData: WorkflowIODefinition[] = [];

    for (const input of workflowTransformation.content.inputs) {
      this.generateWorkflowIODefinition(
        input,
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

    const form = this.formBuilder.group({
      operator: data.operator,
      connector: data.connector,
      type: data.type,
      isConstant: data.isConstant,
      id: data.id,
      constant: constantControl,
      name: nameControl
    });

    nameControl.valueChanges.subscribe(() => {
      this.updateWorkflowIO(form.getRawValue());
    });

    constantControl.valueChanges.subscribe(() => {
      this.updateWorkflowIO(form.getRawValue());
    });

    return form;
  }

  private generateWorkflowIODefinition(
    workflowIO: IOConnector,
    workflowTransformation: WorkflowTransformation,
    dataArray: WorkflowIODefinition[]
  ): void {
    const operator = workflowTransformation.content.operators.find(
      op => op.id === workflowIO.operator_id
    );
    if (operator === undefined) {
      throw new Error(
        `Could not find operator with id '${workflowIO.operator_id}'`
      );
    }
    let connector = operator.inputs.find(
      io => io.id === workflowIO.connector_id
    );
    if (connector === undefined) {
      connector = operator.outputs.find(
        io => io.id === workflowIO.connector_id
      );
    }
    if (connector === undefined) {
      throw new Error(
        `Could not find connector with id '${workflowIO.connector_id}'`
      );
    }
    const constant = workflowTransformation.content.constants.find(
      cons =>
        cons.operator_id === workflowIO.operator_id &&
        cons.connector_id === workflowIO.connector_id
    );
    if (constant === undefined) {
      throw new Error(
        `Could not find constant with operator id '${workflowIO.operator_id}' and  connector id '${workflowIO.connector_id}'`
      );
    }
    const data = new WorkflowIODefinition(
      workflowIO,
      operator,
      connector,
      constant
    );

    dataArray.push(data);
  }

  toggleConstant(workflowIODefinitionForm: AbstractControl): void {
    const isConstantControl = workflowIODefinitionForm.get('isConstant');
    isConstantControl.setValue(!isConstantControl.value);

    const isConstant = isConstantControl.value;
    const constantControl = workflowIODefinitionForm.get('constant');
    const nameControl = workflowIODefinitionForm.get('name');

    const rawValue = (workflowIODefinitionForm as FormGroup).getRawValue() as WorkflowIODefinition;

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
    console.log('update io: ' + data)
    const input:
      | IOConnector
      | undefined = this.data.workflowTransformation.content.inputs.find(
      (ref: IOConnector) => ref.id === data.id
    );
    const output:
      | IOConnector
      | undefined = this.data.workflowTransformation.content.outputs.find(
      (ref: IOConnector) => ref.id === data.id
    );
    if (input !== undefined) {
      // input.constantValue = { value: data.constant };
      // input.name = data.name;
      // input.constant = data.isConstant;
    }
    if (output !== undefined) {
      // output.constantValue = { value: data.constant };
      // output.name = data.name;
      // output.constant = data.isConstant;
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
    console.log('workflow preview');
    if (this.data.workflowTransformation === undefined) {
      return;
    }
    this.preview = this.flowchartConverter.convertComponentToFlowchart(
      this.data.workflowTransformation as Transformation
    );
  }
}
