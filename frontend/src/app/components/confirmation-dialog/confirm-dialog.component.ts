import { Component, Inject } from '@angular/core';
import { MatDialogRef, MAT_DIALOG_DATA } from '@angular/material/dialog';

export interface CheckboxOption {
  label: string;
  checked: boolean;
  key: string; // Unique identifier for each checkbox
}

export interface ConfirmDialogData {
  title: string;
  actionCancel: string;
  actionOk: string;
  content: string;
  checkboxes?: CheckboxOption[]; // Optional array of checkboxes
}

export interface ConfirmDialogResult {
  confirmed: boolean;
  checkboxValues?: { [key: string]: boolean }; // Checkbox states by key
}
@Component({
  selector: 'hd-confirm-dialog-modal',
  templateUrl: 'confirm-dialog.component.html'
})
export class ConfirmDialogComponent {
  constructor(
    public dialogRef: MatDialogRef<ConfirmDialogComponent>,
    @Inject(MAT_DIALOG_DATA) public data: ConfirmDialogData
  ) {}

  onCancel(): void {
    this.dialogRef.close({ confirmed: false });
  }

  onOk(): void {
    const result: ConfirmDialogResult = {
      confirmed: true
    };

    // If checkboxes exist, collect their values
    if (this.data.checkboxes && this.data.checkboxes.length > 0) {
      result.checkboxValues = {};
      this.data.checkboxes.forEach(checkbox => {
        result.checkboxValues[checkbox.key] = checkbox.checked;
      });
    }

    this.dialogRef.close(result);
  }
}
