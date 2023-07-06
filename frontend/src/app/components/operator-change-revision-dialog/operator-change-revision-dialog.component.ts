import { Component, Inject, OnInit } from '@angular/core';
import { MAT_DIALOG_DATA, MatDialogRef } from '@angular/material/dialog';
import { Transformation } from 'src/app/model/transformation';

export interface OperatorChangeRevisionDialogData {
  revisions: Transformation[];
}

@Component({
  selector: 'hd-operator-change-revision-dialog',
  templateUrl: './operator-change-revision-dialog.component.html',
  styleUrls: ['./operator-change-revision-dialog.component.scss']
})
export class OperatorChangeRevisionDialogComponent implements OnInit {
  public selectedRevision: Transformation | null = null;

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
