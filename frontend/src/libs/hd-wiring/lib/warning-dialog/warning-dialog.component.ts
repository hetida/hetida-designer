import { Component, Inject, OnInit } from '@angular/core';
import { MAT_DIALOG_DATA } from '@angular/material/dialog';

@Component({
  selector: 'lib-warning-dialog',
  templateUrl: './warning-dialog.component.html',
  styleUrls: ['./warning-dialog.component.css'],
  standalone: false
})
export class WarningDialogComponent implements OnInit {
  _errorMessage: string | undefined;

  constructor(@Inject(MAT_DIALOG_DATA) public data: any) {}

  ngOnInit(): void {
    console.warn('Wiring Warning', this.data);
    if (this.data.error) {
      this._errorMessage = `Warning on ${
        this.data.error.workflow_input_name
          ? `input with label "${this.data.error.workflow_input_name}"`
          : `output with label "${this.data.error.workflow_output_name}"`
      } from source "${this.data.error.adapter_id}" on "${
        this.data.error.ref_id
      }" with "${this.data.error.ref_key}"`;
    }
  }
}
