import { Component, HostListener, Inject } from '@angular/core';
import { MatIcon } from '@angular/material/icon';
import {
  MAT_SNACK_BAR_DATA,
  MatSnackBarLabel,
  MatSnackBarRef
} from '@angular/material/snack-bar';

/**
 * A notification message part is either plain text or a Material icon,
 * e.g. to show the toolbar button a message refers to.
 */
export type NotificationMessagePart = string | { icon: string };

/**
 * Content of all notification snack bars. Clicking the message closes it.
 */
@Component({
  selector: 'hd-notification-message',
  templateUrl: './notification-message.component.html',
  styleUrls: ['./notification-message.component.scss'],
  standalone: true,
  imports: [MatIcon, MatSnackBarLabel]
})
export class NotificationMessageComponent {
  constructor(
    @Inject(MAT_SNACK_BAR_DATA) public parts: NotificationMessagePart[],
    private readonly snackBarRef: MatSnackBarRef<NotificationMessageComponent>
  ) {}

  isIcon(part: NotificationMessagePart): part is { icon: string } {
    return typeof part !== 'string';
  }

  @HostListener('click')
  close(): void {
    // Selecting text, e.g. to copy an error message, must not close it.
    if (window.getSelection()?.toString()) {
      return;
    }
    this.snackBarRef.dismiss();
  }
}
