import { Overlay } from '@angular/cdk/overlay';
import { TestBed } from '@angular/core/testing';
import { MatSnackBar } from '@angular/material/snack-bar';
import { NotificationMessageComponent } from '../../components/notification-message/notification-message.component';
import {
  NotificationMessage,
  NotificationService
} from './notification.service';

describe('NotificationsService', () => {
  let service: NotificationService;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [NotificationService, MatSnackBar, Overlay]
    });
    service = TestBed.inject(NotificationService);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });

  it('default method should be executable', () => {
    spyOn(service, 'default');
    service.default('default message');
    expect(service.default).toHaveBeenCalled();
  });

  it('info method should be executable', () => {
    spyOn(service, 'info');
    service.info('info message');
    expect(service.info).toHaveBeenCalled();
  });

  it('success method should be executable', () => {
    spyOn(service, 'success');
    service.success('success message');
    expect(service.success).toHaveBeenCalled();
  });

  it('warning method should be executable', () => {
    spyOn(service, 'warn');
    service.warn('warning message');
    expect(service.warn).toHaveBeenCalled();
  });

  it('error method should be executable', () => {
    spyOn(service, 'error');
    service.error('error message');
    expect(service.error).toHaveBeenCalled();
  });

  it('opens plain text messages via the notification message component', () => {
    const snackBar = TestBed.inject(MatSnackBar);
    spyOn(snackBar, 'openFromComponent');

    service.warn('warning message');

    expect(snackBar.openFromComponent).toHaveBeenCalledWith(
      NotificationMessageComponent,
      jasmine.objectContaining({
        data: ['warning message'],
        panelClass: 'warning-notification-overlay'
      })
    );
  });

  it('opens messages with icons via the notification message component', () => {
    const snackBar = TestBed.inject(MatSnackBar);
    spyOn(snackBar, 'openFromComponent');
    const message = ['Click ', { icon: 'auto_awesome' }, '.'];

    service.warn(message);

    expect(snackBar.openFromComponent).toHaveBeenCalledWith(
      NotificationMessageComponent,
      jasmine.objectContaining({
        data: message,
        panelClass: 'warning-notification-overlay'
      })
    );
  });

  describe('duration', () => {
    let openFromComponent: jasmine.Spy;

    beforeEach(() => {
      openFromComponent = spyOn(
        TestBed.inject(MatSnackBar),
        'openFromComponent'
      );
    });

    const durationOf = (message: NotificationMessage): number => {
      service.info(message);
      return openFromComponent.calls.mostRecent().args[1].duration;
    };

    it('is 5 seconds for short messages', () => {
      expect(durationOf('x'.repeat(19))).toBe(5000);
    });

    it('grows by one second for every 20 characters', () => {
      expect(durationOf('x'.repeat(20))).toBe(6000);
      expect(durationOf('x'.repeat(59))).toBe(7000);
      expect(durationOf('x'.repeat(200))).toBe(15000);
    });

    it('is at most 20 seconds', () => {
      expect(durationOf('x'.repeat(299))).toBe(19000);
      expect(durationOf('x'.repeat(300))).toBe(20000);
      expect(durationOf('x'.repeat(320))).toBe(20000);
      expect(durationOf('x'.repeat(5000))).toBe(20000);
    });

    it('counts the text as shown, without icons and collapsed whitespace', () => {
      expect(
        durationOf(['x'.repeat(10), { icon: 'auto_awesome' }, 'x'.repeat(9)])
      ).toBe(5000);
      // 19 characters as shown, 49 as written.
      expect(
        durationOf(`${'x'.repeat(10)}\n${' '.repeat(30)}${'x'.repeat(8)}`)
      ).toBe(5000);
    });
  });
});
