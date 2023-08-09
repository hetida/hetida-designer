import { Component, Inject } from '@angular/core';
import { MAT_DIALOG_DATA, MatDialogRef } from '@angular/material/dialog';
import { Operator } from '../../model/operator';
import { FormArray, FormBuilder, FormGroup } from '@angular/forms';
import { IOTypeOption } from 'hetida-flowchart';

export interface OptionalFieldsDialogData {
  operator: Operator;
  actionOk: string;
  actionCancel: string;
}

@Component({
  selector: 'hd-optional-fields-dialog',
  templateUrl: './optional-fields-dialog.component.html',
  styleUrls: ['./optional-fields-dialog.component.scss']
})
export class OptionalFieldsDialogComponent {
  optionalFieldsForm: FormGroup;
  workflowName: string;

  get optionalFieldsArray(): FormArray {
    return this.optionalFieldsForm.get('inputs') as FormArray;
  }

  constructor(
    private readonly dialogRef: MatDialogRef<OptionalFieldsDialogComponent>,
    @Inject(MAT_DIALOG_DATA) public data: OptionalFieldsDialogData,
    private readonly formBuilder: FormBuilder
  ) {
    this.workflowName = this.data.operator.name;
    this.optionalFieldsForm = this.formBuilder.group({
      inputs: this.formBuilder.array(
        this.data.operator.inputs
          .filter(input => input.type === IOTypeOption.OPTIONAL)
          .map(input => {
            const exposedControl = this.formBuilder.control(input.exposed);
            exposedControl.valueChanges.subscribe(exposedValue => {
              this.data.operator.inputs.forEach(inp => {
                if (inp.id === input.id) {
                  inp.exposed = exposedValue;
                }
              });
            });

            return this.formBuilder.group({
              name: input.name,
              exposed: exposedControl,
              value: input.value
            });
          })
      )
    });
  }

  get valid(): boolean {
    return this.optionalFieldsForm.valid;
  }

  onCancel(): void {
    this.dialogRef.close();
  }

  onOk(): void {
    this.dialogRef.close(this.data.operator.inputs);
  }
}
