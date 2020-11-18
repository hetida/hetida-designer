import { Component, Inject, OnInit } from '@angular/core';
import { MAT_DIALOG_DATA, MatDialogRef } from '@angular/material/dialog';
import { AbstractBaseItem } from 'src/app/model/base-item';

export interface OperatorChangeRevisionDialogData {
  revisions: AbstractBaseItem[];
}

@Component({
  selector: 'hd-operator-change-revision-dialog',
  templateUrl: './operator-change-revision-dialog.component.html',
  styleUrls: ['./operator-change-revision-dialog.component.scss']
})
export class OperatorChangeRevisionDialogComponent implements OnInit {
  public selectedRevision: AbstractBaseItem | null = null;

  constructor(
    public dialogRef: MatDialogRef<OperatorChangeRevisionDialogComponent>,
    @Inject(MAT_DIALOG_DATA) public data: OperatorChangeRevisionDialogData
  ) {}

  ngOnInit() {}

  onCancel(): void {
    this.dialogRef.close();
  }

  onOk(): void {
    if (this.selectedRevision === null) {
      this.dialogRef.close();
    } else {
      this.dialogRef.close(this.selectedRevision);
    }
  }
}
