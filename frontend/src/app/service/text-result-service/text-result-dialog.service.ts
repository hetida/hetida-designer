import { Injectable } from '@angular/core';
import { MatDialog } from '@angular/material/dialog';
import { TextResultDialogComponent } from '../../components/text-result-dialog/text-result-dialog.component';

@Injectable({
  providedIn: 'root'
})
export class TextResultDialogService {
  constructor(private readonly dialog: MatDialog) {}

  openDialog(title: string, message: string) {
    return this.dialog.open(TextResultDialogComponent, {
      data: { title, message },
      disableClose: true
    });
  }
}
