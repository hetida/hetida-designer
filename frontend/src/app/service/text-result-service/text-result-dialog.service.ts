import { Injectable } from '@angular/core';
import { MatDialog } from '@angular/material/dialog';
import { Observable } from 'rxjs';
import { TextResultDialogComponent } from '../../components/text-result-dialog/text-result-dialog.component';

@Injectable({
  providedIn: 'root'
})
export class TextResultDialogService {
  constructor(private readonly dialog: MatDialog) {}

  openDialog(title: string, message: string, width = '95vh') {
    return this.dialog.open(TextResultDialogComponent, {
      width,
      data: { title, message }
    });
  }

  /**
   * Opens the dialog immediately, showing a loading spinner until
   * the provided observable emits the message to display.
   */
  openDialogWithLoading(
    title: string,
    message$: Observable<string>,
    loadingText?: string,
    width = '95vh'
  ) {
    return this.dialog.open(TextResultDialogComponent, {
      width,
      data: { title, message$, loadingText }
    });
  }
}
