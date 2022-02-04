import { Component, Inject, OnInit } from '@angular/core';
import { FormArray, FormBuilder, FormGroup, Validators } from '@angular/forms';
import { MAT_DIALOG_DATA, MatDialogRef } from '@angular/material/dialog';
import {
  createReadOnlyConfig,
  FlowchartConfiguration,
  SVGManipulatorConfiguration
} from 'hetida-flowchart';
import { IOType } from 'hetida-flowchart/types/IOType';
import { ComponentBaseItem } from 'src/app/model/component-base-item';
import { FlowchartConverterService } from 'src/app/service/type-converter/flowchart-converter.service';
import { PythonIdentifierValidator } from 'src/app/validation/python-identifier-validator';
import { PythonKeywordBlacklistValidator } from 'src/app/validation/python-keyword-validator';
import { UniqueValueValidator } from 'src/app/validation/unique-value-validator';
import { v4 as UUID } from 'uuid';
import { IOItem } from '../../model/io-item';

export interface ComponentIoDialogData {
  componentBaseItem: ComponentBaseItem;
  editMode: boolean;
  actionOk: string;
  actionCancel: string;
}

@Component({
  selector: 'hd-component-new-revision-modal',
  templateUrl: 'component-io-dialog.component.html',
  styleUrls: ['component-io-dialog.component.scss']
})
export class ComponentIODialogComponent implements OnInit {
  componentBaseItem: ComponentBaseItem;

  _preview: FlowchartConfiguration = {
    id: '',
    components: [],
    io: [],
    links: []
  };

  _svgConfiguration: SVGManipulatorConfiguration;

  readonly _ioTypes = Object.keys(IOType);

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
    private readonly _flowchartConverter: FlowchartConverterService,
    private readonly _formBuilder: FormBuilder
  ) {
    this.componentBaseItem = this.data.componentBaseItem;

    this._svgConfiguration = createReadOnlyConfig(
      new SVGManipulatorConfiguration()
    );
    this._svgConfiguration.allowPanning = false;
    this._svgConfiguration.allowZooming = false;
    this._svgConfiguration.showContextMenu = false;
    this._createPreview();
  }

  ngOnInit(): void {
    this._setupFormControl();
  }

  private _setupFormControl(): void {
    const inputIOControls = this.componentBaseItem.inputs.map(
      this._createIOItemControl.bind(this)
    );
    const outputIOControls = this.componentBaseItem.outputs.map(
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

  private _createIOItemControl(input: IOItem): FormGroup {
    return this._formBuilder.group({
      name: this._createNameControl(input),
      type: this._createTypeControl(input),
      id: this._formBuilder.control({ value: input.id, disabled: true })
    });
  }

  _removeInput(index: number, ioId: string) {
    this._ioItemInputsFormArray.removeAt(index);
    this.componentBaseItem.inputs = this.componentBaseItem.inputs.filter(
      ioItem => ioItem.id !== ioId
    );
    this._createPreview();
  }

  _removeOutput(index: number, ioId: string) {
    this._ioItemOutputsFormArray.removeAt(index);
    this.componentBaseItem.outputs = this.componentBaseItem.outputs.filter(
      ioItem => ioItem.id !== ioId
    );
    this._createPreview();
  }

  _inputAdd(): void {
    const io: IOItem = {
      id: UUID().toString(),
      name: this._computeNextAvailableName(
        'new_input',
        this.componentBaseItem.inputs
      ),
      type: IOType.ANY,
      posX: 0,
      posY: 0
    };
    this.componentBaseItem.inputs.push(io);
    this._createPreview();
    this._setupFormControl();
  }

  _outputAdd(): void {
    const io: IOItem = {
      id: UUID().toString(),
      name: this._computeNextAvailableName(
        'new_output',
        this.componentBaseItem.outputs
      ),
      type: IOType.ANY,
      posX: 0,
      posY: 0
    };
    this.componentBaseItem.outputs.push(io);
    this._createPreview();
    this._setupFormControl();
  }

  _onOk(): void {
    if (this.data.editMode === false) {
      this.dialogRef.close();
    } else {
      this.dialogRef.close(this.componentBaseItem);
    }
  }

  _onCancel(): void {
    this.dialogRef.close();
  }

  private _createPreview(): void {
    if (this.componentBaseItem === undefined) {
      return;
    }
    this._preview = this._flowchartConverter.convertComponentToFlowchart(
      this.componentBaseItem
    );
  }

  private _computeNextAvailableName(prefix: string, list: IOItem[]) {
    if (list === undefined) {
      return `${prefix}_1`;
    }

    let count = 1;
    while (list.find(io => io.name === `${prefix}_${count}`) !== undefined) {
      count++;
    }
    return `${prefix}_${count}`;
  }

  private _createNameControl(io: IOItem) {
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

  private _createTypeControl(io: IOItem) {
    const control = this._formBuilder.control(
      {
        value: io.type,
        disabled: !this.data.editMode
      },
      [Validators.required]
    );
    control.valueChanges.subscribe(changes => {
      io.type = changes;
      this._createPreview();
    });
    return control;
  }
}
