import { ErrorHandler, Injectable } from '@angular/core';
import { HttpErrorResponse } from '@angular/common/http';

import { environment } from '../../../environments/environment';

import { NotificationService } from '../notifications/notification.service';

/** Application-wide error handler that adds a UI notification to the error handling
 * provided by the default Angular ErrorHandler.
 */
@Injectable()
export class AppErrorHandler extends ErrorHandler {
  /** Detects Monaco's cancellation error (name/message === 'Canceled'),
   * including the case where Angular wraps it in `ngOriginalError`.
   */
  private static isCancellationError(error: unknown): boolean {
    const candidate =
      error && (error as { ngOriginalError?: unknown }).ngOriginalError
        ? (error as { ngOriginalError: unknown }).ngOriginalError
        : error;
    if (!(candidate instanceof Error)) {
      return false;
    }
    return candidate.name === 'Canceled' || candidate.message === 'Canceled';
  }

  constructor(private readonly notificationsService: NotificationService) {
    super();
  }

  handleError(error: Error | HttpErrorResponse) {
    // Monaco editor rejects pending async operations (link providers,
    // tokenization, worker requests) with a cancellation error when its
    // editor instance is disposed, e.g. when a component transformation tab
    // is closed. These are benign internals and must not surface as errors.
    if (AppErrorHandler.isCancellationError(error)) {
      return;
    }

    let displayMessage = 'An error occurred.';

    if (!environment.production) {
      displayMessage += ' See console for details.';
    }

    this.notificationsService.error(displayMessage);

    super.handleError(error);
  }
}
