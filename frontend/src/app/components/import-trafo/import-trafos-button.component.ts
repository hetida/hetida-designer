import { Component } from '@angular/core';
import { MatDialog } from '@angular/material/dialog';
import { ImportDialogComponent } from './import-trafo-dialog.component';

@Component({
  selector: 'hd-import-trafos-button',
  templateUrl: './import-trafos-button.component.html',
  standalone: false
})
export class ImportTrafosButtonComponent {
  constructor(private readonly matDialog: MatDialog) {}

  openImportDialog(): void {
    this.matDialog.open(ImportDialogComponent, {
      width: '700px',
      disableClose: true
    });
  }
}
