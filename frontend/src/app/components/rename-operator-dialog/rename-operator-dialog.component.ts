import { Component, Inject, OnInit } from '@angular/core';
import { FormControl, Validators } from '@angular/forms';
import { MatDialogRef, MAT_DIALOG_DATA } from '@angular/material/dialog';
import { Operator } from 'src/app/model/new-api/operator';

export interface RenameOperatorDialogData {
  operator: Operator;
}

@Component({
  selector: 'hd-rename-operator-dialog',
  templateUrl: './rename-operator-dialog.component.html',
  styleUrls: ['./rename-operator-dialog.component.scss']
})
export class RenameOperatorDialogComponent implements OnInit {
  constructor(
    public dialogRef: MatDialogRef<
      RenameOperatorDialogComponent,
      string | undefined
    >,
    @Inject(MAT_DIALOG_DATA) public data: RenameOperatorDialogData
  ) {}

  public name: FormControl = new FormControl(this.data.operator.name, [
    Validators.required,
    Validators.maxLength(60)
  ]);

  ngOnInit() {}

  onCancel(): void {
    this.dialogRef.close();
  }

  onOk(): void {
    this.dialogRef.close(this.name.value);
  }
}
