import { Component, Inject, OnDestroy, OnInit } from '@angular/core';
import {
  MAT_DIALOG_DATA,
  MatDialogRef,
  MatDialogContent,
  MatDialogActions,
  MatDialogTitle
} from '@angular/material/dialog';
import { MatButtonModule } from '@angular/material/button';
import { MatIcon } from '@angular/material/icon';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { Observable, Subscription } from 'rxjs';

interface DialogData {
  title: string;
  message?: string;
  // If provided, the dialog shows a loading spinner until the message arrives.
  message$?: Observable<string>;
  loadingText?: string;
}

@Component({
  selector: 'app-result-dialog',
  templateUrl: './text-result-dialog.component.html',
  styleUrls: ['./text-result-dialog.component.scss'],
  standalone: true,
  imports: [
    MatDialogContent,
    MatDialogActions,
    MatDialogTitle,
    MatButtonModule,
    MatIcon,
    MatProgressSpinnerModule
  ]
})
export class TextResultDialogComponent implements OnInit, OnDestroy {
  loading = false;
  message: string | undefined;

  private messageSubscription: Subscription | undefined;

  constructor(
    public dialogRef: MatDialogRef<TextResultDialogComponent>,
    @Inject(MAT_DIALOG_DATA) public data: DialogData
  ) {}

  ngOnInit(): void {
    if (this.data.message$ !== undefined) {
      this.loading = true;
      this.messageSubscription = this.data.message$.subscribe({
        next: message => {
          this.message = message;
          this.loading = false;
        },
        error: () => {
          this.message =
            'An error occurred. See notifications or browser console for details.';
          this.loading = false;
        }
      });
    } else {
      this.message = this.data.message;
    }
  }

  ngOnDestroy(): void {
    this.messageSubscription?.unsubscribe();
  }

  _close(): void {
    this.dialogRef.close();
  }
}
