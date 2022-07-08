import { Injectable, NgZone } from '@angular/core';
import { MatSnackBar, MatSnackBarConfig } from '@angular/material/snack-bar';

@Injectable({
  providedIn: 'root'
})
export class NotificationService {
  private readonly notificationOptions: MatSnackBarConfig = {
    verticalPosition: 'top',
    horizontalPosition: 'right',
    duration: 5000
  };

  constructor(
    private readonly snackBar: MatSnackBar,
    private readonly zone: NgZone
  ) {}

  default(message: string) {
    this.show(message, {
      ...this.notificationOptions,
      panelClass: 'default-notification-overlay'
    });
  }

  info(message: string) {
    this.show(message, {
      ...this.notificationOptions,
      panelClass: 'info-notification-overlay'
    });
  }

  success(message: string) {
    this.show(message, {
      ...this.notificationOptions,
      panelClass: 'success-notification-overlay'
    });
  }

  warn(message: string) {
    this.show(message, {
      ...this.notificationOptions,
      panelClass: 'warning-notification-overlay'
    });
  }

  error(message: string) {
    this.show(message, {
      ...this.notificationOptions,
      panelClass: 'error-notification-overlay'
    });
  }

  private show(message: string, configuration: MatSnackBarConfig) {
    // Need to open snackBar from Angular zone to prevent issues with its position per
    // https://stackoverflow.com/questions/50101912/snackbar-position-wrong-when-use-errorhandler-in-angular-5-and-material
    this.zone.run(() => this.snackBar.open(message, null, configuration));
  }
}
