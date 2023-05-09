import { Component, Inject } from '@angular/core';
import { MAT_DIALOG_DATA, MatDialogRef } from '@angular/material/dialog';
import { Operator } from '../../model/operator';
import { FormArray, FormBuilder, FormGroup } from '@angular/forms';
import { IOTypeOption } from '../../../../../../../hetida-flowchart/packages/hetida-flowchart/dist';

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

  get optionalFieldsArray(): FormArray {
    return this.optionalFieldsForm.get('inputs') as FormArray;
  }

  constructor(
    private readonly dialogRef: MatDialogRef<OptionalFieldsDialogComponent>,
    @Inject(MAT_DIALOG_DATA) public data: OptionalFieldsDialogData,
    private readonly formBuilder: FormBuilder
  ) {
    this.optionalFieldsForm = this.formBuilder.group({
      inputs: this.formBuilder.array(
        this.data.operator.inputs
          .filter(input => input.type === IOTypeOption.OPTIONAL)
          .map(input => {
            let exposed = input.exposed;
            if (input.type === IOTypeOption.OPTIONAL && input.value) {
              exposed = true;
            }
            const exposedControl = this.formBuilder.control({
              value: exposed,
              disabled: input.type === IOTypeOption.OPTIONAL && input.value
            });

            exposedControl.valueChanges.subscribe(exposedValue => {
              this.data.operator.inputs.forEach(inp => {
                if (inp.id === input.id) {
                  inp.exposed = exposedValue;
                }
              });
            });

            return this.formBuilder.group({
              name: input.name,
              exposed: exposedControl
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
