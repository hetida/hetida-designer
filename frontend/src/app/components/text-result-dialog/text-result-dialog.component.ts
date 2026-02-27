import { Component, Inject } from '@angular/core';
import { MAT_DIALOG_DATA, MatDialogRef } from '@angular/material/dialog';

interface DialogData {
  title: string;
  message: string;
}

@Component({
  selector: 'app-result-dialog',
  templateUrl: './text-result-dialog.component.html',
  styleUrls: ['./text-result-dialog.component.scss'],
  standalone: false
})
export class TextResultDialogComponent {
  constructor(
    public dialogRef: MatDialogRef<TextResultDialogComponent>,
    @Inject(MAT_DIALOG_DATA) public data: DialogData
  ) {}

  close(): void {
    this.dialogRef.close();
  }
}
