import { Injectable } from '@angular/core';
import { MatDialog } from '@angular/material/dialog';
import { ResultDialogComponent } from '../../components/result-dialog/result-dialog.component';

@Injectable({
  providedIn: 'root'
})
export class ResultDialogService {
  constructor(private readonly dialog: MatDialog) {}

  openDialog(title: string, message: string) {
    return this.dialog.open(ResultDialogComponent, {
      data: { title, message },
      disableClose: true
    });
  }
}
