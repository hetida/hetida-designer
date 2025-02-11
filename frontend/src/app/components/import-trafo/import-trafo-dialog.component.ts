// import-dialog.component.ts
import { Component } from '@angular/core';
import { MatDialogRef } from '@angular/material/dialog';
import { TransformationService } from '../../service/transformation/transformation.service';

import { TextResultDialogService } from '../../service/text-result-service/text-result-dialog.service';
import { NotificationService } from '../../service/notifications/notification.service';

@Component({
  selector: 'app-import-dialog',
  templateUrl: './import-trafo-dialog.component.html',
  styleUrls: ['./import-trafo-dialog.component.scss']
})
export class ImportDialogComponent {
  importText = '';
  updateCode = false;
  expandCode = false;
  overwriteReleased = false;
  message = '';

  constructor(
    private readonly dialogRef: MatDialogRef<ImportDialogComponent>,
    private readonly transformationService: TransformationService,
    private readonly resultDialogService: TextResultDialogService,
    private readonly notificationService: NotificationService
  ) {}

  closeDialog(): void {
    this.dialogRef.close();
  }

  onCancel(): void {
    this.dialogRef.close(false);
  }

  importTrafos(): void {
    if (!this.importText.trim()) {
      return;
    }

    this.transformationService
      .importTrafoRevFromString(
        this.importText.trim(),
        this.updateCode,
        this.expandCode,
        this.overwriteReleased
      )
      .subscribe({
        next: response => {
          // Handle successful import
          const resp_str = JSON.stringify(response);
          this.transformationService.fetchAllTransformations();
          this.message = resp_str;
          this.resultDialogService.openDialog(
            'Import Trafo Report',
            this.message
          );
        },
        error: error => {
          // Handle error
          this.notificationService.warn(`Trafo Import failed: ${error}`);
        }
      });
  }
}
