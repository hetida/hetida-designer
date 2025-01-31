import { Component } from '@angular/core';
import { MatDialog } from '@angular/material/dialog';
import { ImportDialogComponent } from './import-trafo-dialog.component';

@Component({
  selector: 'app-import-button',
  template: `
    <mat-icon
      class="clickable unselectable"
      title="Import Transformation Revisions"
      (click)="openImportDialog()"
    >
      upload</mat-icon
    >
  `
})
export class ImportButtonComponent {
  constructor(private readonly importTrafoDialog: MatDialog) {}

  openImportDialog(): void {
    this.importTrafoDialog.open(ImportDialogComponent, {
      width: '700px',
      disableClose: true
    });
  }
}
