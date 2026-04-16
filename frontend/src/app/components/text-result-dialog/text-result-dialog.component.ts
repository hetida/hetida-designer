import { Component, Inject } from '@angular/core';

import {
  MAT_DIALOG_DATA,
  MatDialogRef,
  MatDialogContent,
  MatDialogActions,
  MatDialogTitle
} from '@angular/material/dialog';
import { MatButtonModule } from '@angular/material/button';
interface DialogData {
  title: string;
  message: string;
}

@Component({
  selector: 'app-result-dialog',
  templateUrl: './text-result-dialog.component.html',
  styleUrls: ['./text-result-dialog.component.scss'],
  standalone: true,
  imports: [MatDialogContent, MatDialogActions, MatDialogTitle, MatButtonModule]
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
