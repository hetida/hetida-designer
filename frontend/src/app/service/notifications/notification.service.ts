import { Injectable, NgZone } from '@angular/core';
import { MatSnackBar, MatSnackBarConfig } from '@angular/material/snack-bar';
import {
  NotificationMessageComponent,
  NotificationMessagePart
} from '../../components/notification-message/notification-message.component';

/**
 * Plain text, or text interspersed with icons (e.g. a toolbar button the
 * message refers to).
 */
export type NotificationMessage = string | NotificationMessagePart[];

/** Time to notice a notification at all, and the duration of short ones. */
const BASE_DURATION_MS = 5000;

/**
 * Text length for which a notification is shown one second longer. A typical
 * silent reading speed for English text is about 230 words or 1200 characters
 * per minute, i.e. 20 characters per second.
 */
const CHARACTERS_PER_ADDITIONAL_SECOND = 20;

/** Long messages, e.g. with error details, can still be closed by a click. */
const MAX_DURATION_MS = 20000;

@Injectable({
  providedIn: 'root'
})
export class NotificationService {
  private readonly notificationOptions: MatSnackBarConfig = {
    verticalPosition: 'top',
    horizontalPosition: 'right'
  };

  constructor(
    private readonly snackBar: MatSnackBar,
    private readonly zone: NgZone
  ) {}

  default(message: NotificationMessage) {
    this.show(message, {
      ...this.notificationOptions,
      panelClass: 'default-notification-overlay'
    });
  }

  info(message: NotificationMessage) {
    this.show(message, {
      ...this.notificationOptions,
      panelClass: 'info-notification-overlay'
    });
  }

  success(message: NotificationMessage) {
    this.show(message, {
      ...this.notificationOptions,
      panelClass: 'success-notification-overlay'
    });
  }

  warn(message: NotificationMessage) {
    this.show(message, {
      ...this.notificationOptions,
      panelClass: 'warning-notification-overlay'
    });
  }

  error(message: NotificationMessage) {
    this.show(message, {
      ...this.notificationOptions,
      panelClass: 'error-notification-overlay'
    });
  }

  private show(message: NotificationMessage, configuration: MatSnackBarConfig) {
    const parts = typeof message === 'string' ? [message] : message;
    // Need to open snackBar from Angular zone to prevent issues with its position per
    // https://stackoverflow.com/questions/50101912/snackbar-position-wrong-when-use-errorhandler-in-angular-5-and-material
    this.zone.run(() =>
      this.snackBar.openFromComponent(NotificationMessageComponent, {
        ...configuration,
        duration: this.durationFor(parts),
        data: parts
      })
    );
  }

  private durationFor(parts: NotificationMessagePart[]): number {
    // Count the text as shown, i.e. without icons and with whitespace collapsed.
    const textLength = parts
      .filter((part): part is string => typeof part === 'string')
      .join('')
      .replace(/\s+/g, ' ')
      .trim().length;
    const additionalSeconds = Math.floor(
      textLength / CHARACTERS_PER_ADDITIONAL_SECOND
    );
    return Math.min(
      BASE_DURATION_MS + additionalSeconds * 1000,
      MAX_DURATION_MS
    );
  }
}
