import { AfterViewInit, Component, Inject } from '@angular/core';
import {
  AbstractControl,
  FormArray,
  FormBuilder,
  FormGroup,
  Validators
} from '@angular/forms';
import { MAT_DIALOG_DATA, MatDialogRef } from '@angular/material/dialog';
import {
  createReadOnlyConfig,
  FlowchartConfiguration,
  IOTypeOption,
  SVGManipulatorConfiguration
} from 'hetida-flowchart';
import { IOType } from 'hetida-flowchart/types/IOType';
import { FlowchartConverterService } from 'src/app/service/type-converter/flowchart-converter.service';
import { PythonIdentifierValidator } from 'src/app/validation/python-identifier-validator';
import { PythonKeywordBlacklistValidator } from 'src/app/validation/python-keyword-validator';
import { UniqueValueValidator } from 'src/app/validation/unique-value-validator';
import { v4 as UUID } from 'uuid';
import { ComponentTransformation } from '../../model/transformation';
import { IO } from 'hd-wiring';

export interface ComponentIoDialogData {
  componentTransformation: ComponentTransformation;
  editMode: boolean;
  actionOk: string;
  actionCancel: string;
}

@Component({
  selector: 'hd-component-new-revision-modal',
  templateUrl: 'component-io-dialog.component.html',
  styleUrls: ['component-io-dialog.component.scss']
})
export class ComponentIODialogComponent implements AfterViewInit {
  componentTransformation: ComponentTransformation;

  _preview: FlowchartConfiguration = {
    id: '',
    components: [],
    io: [],
    links: []
  };

  _svgConfiguration: SVGManipulatorConfiguration;

  readonly _ioTypes = Object.keys(IOType);
  readonly _ioTypeOptions = Object.keys(IOTypeOption);

  _ioItemForm: FormGroup;

  get _ioItemInputsFormArray(): FormArray {
    return this._ioItemForm.get('inputs') as FormArray;
  }

  get _ioItemOutputsFormArray(): FormArray {
    return this._ioItemForm.get('outputs') as FormArray;
  }

  constructor(
    public dialogRef: MatDialogRef<ComponentIODialogComponent>,
    @Inject(MAT_DIALOG_DATA) public data: ComponentIoDialogData,
    // @ts-ignore
    private readonly _flowchartConverter: FlowchartConverterService,
    private readonly _formBuilder: FormBuilder
  ) {
    this.componentTransformation = this.data.componentTransformation;

    this._svgConfiguration = createReadOnlyConfig(
      new SVGManipulatorConfiguration()
    );
    this._svgConfiguration.allowPanning = false;
    this._svgConfiguration.allowZooming = false;
    this._svgConfiguration.showContextMenu = false;

    this._setupFormControl();
  }

  ngAfterViewInit(): void {
    this._createPreview();
  }

  private _setupFormControl(): void {
    const inputIOControls =
      this.componentTransformation.io_interface.inputs.map(
        this._createIOItemControl.bind(this)
      );
    const outputIOControls =
      this.componentTransformation.io_interface.outputs.map(
        this._createIOItemControl.bind(this)
      );

    this._ioItemForm = this._formBuilder.group({
      inputs: this._formBuilder.array(inputIOControls, {
        validators: UniqueValueValidator('name')
      }),
      outputs: this._formBuilder.array(outputIOControls, {
        validators: UniqueValueValidator('name')
      })
    });
  }

  private _createIOItemControl(input: IO): FormGroup {
    return this._formBuilder.group({
      name: this._createNameControl(input),
      data_type: this._createDataTypeControl(input),
      type: this._createTypeControl(input),
      value: this._createValueControl(input),
      id: this._formBuilder.control({ value: input.id, disabled: true })
    });
  }

  _removeInput(index: number, ioId: string) {
    this._ioItemInputsFormArray.removeAt(index);
    this.componentTransformation.io_interface.inputs =
      this.componentTransformation.io_interface.inputs.filter(
        ioItem => ioItem.id !== ioId
      );
    this._createPreview();
  }

  _removeOutput(index: number, ioId: string) {
    this._ioItemOutputsFormArray.removeAt(index);
    this.componentTransformation.io_interface.outputs =
      this.componentTransformation.io_interface.outputs.filter(
        ioItem => ioItem.id !== ioId
      );
    this._createPreview();
  }

  _inputAdd(): void {
    const io: IO = {
      id: UUID().toString(),
      name: this._computeNextAvailableName(
        'new_input',
        this.componentTransformation.io_interface.inputs
      ),
      data_type: IOType.ANY,
      type: IOTypeOption.REQUIRED,
      value: null,
      exposed: false
    };
    this.componentTransformation.io_interface.inputs.push(io);
    this._createPreview();
    this._setupFormControl();
  }

  _outputAdd(): void {
    const io: IO = {
      id: UUID().toString(),
      name: this._computeNextAvailableName(
        'new_output',
        this.componentTransformation.io_interface.outputs
      ),
      data_type: IOType.ANY,
      type: IOTypeOption.REQUIRED,
      value: ''
    };
    this.componentTransformation.io_interface.outputs.push(io);
    this._createPreview();
    this._setupFormControl();
  }

  _onOk(): void {
    if (this.data.editMode === false) {
      this.dialogRef.close();
    } else {
      this.dialogRef.close(this.componentTransformation);
    }
  }

  _onCancel(): void {
    this.dialogRef.close();
  }

  _isDefaultParameter(ioItem: AbstractControl): boolean {
    return ioItem.get('type').value === IOTypeOption.OPTIONAL;
  }

  _ioTypeOptionChanged(event: IOTypeOption, ioItem: AbstractControl) {
    if (event === IOTypeOption.REQUIRED) {
      ioItem.patchValue({
        value: null
      });
    }
  }

  private _createPreview(): void {
    if (this.componentTransformation === undefined) {
      return;
    }
    this._preview = this._flowchartConverter.convertComponentToFlowchart(
      this.componentTransformation
    );
  }

  private _computeNextAvailableName(prefix: string, list: IO[]) {
    if (list === undefined) {
      return `${prefix}_1`;
    }

    let count = 1;
    while (list.find(io => io.name === `${prefix}_${count}`) !== undefined) {
      count++;
    }
    return `${prefix}_${count}`;
  }

  private _createNameControl(io: IO) {
    const control = this._formBuilder.control(
      {
        value: io.name,
        disabled: !this.data.editMode
      },
      [
        Validators.required,
        Validators.maxLength(60),
        PythonIdentifierValidator(false),
        PythonKeywordBlacklistValidator()
      ]
    );
    control.valueChanges.subscribe(changes => {
      io.name = changes;
      this._createPreview();
    });
    return control;
  }

  private _createDataTypeControl(io: IO) {
    const control = this._formBuilder.control(
      {
        value: io.data_type,
        disabled: !this.data.editMode
      },
      [Validators.required]
    );
    control.valueChanges.subscribe(changes => {
      io.data_type = changes;
      this._createPreview();
    });
    return control;
  }

  private _createTypeControl(io: IO) {
    const control = this._formBuilder.control({
      value: io.type ?? IOTypeOption.REQUIRED,
      disabled: !this.data.editMode
    });
    control.valueChanges.subscribe(changes => {
      io.type = changes;
      this._createPreview();
    });
    return control;
  }

  private _createValueControl(io: IO) {
    const control = this._formBuilder.control({
      value: io.value,
      disabled: !this.data.editMode
    });
    control.valueChanges.subscribe(changes => {
      io.value = changes;
      this._createPreview();
    });
    return control;
  }
}
