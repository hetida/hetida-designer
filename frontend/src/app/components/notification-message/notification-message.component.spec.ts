import { ComponentFixture, TestBed } from '@angular/core/testing';
import {
  MAT_SNACK_BAR_DATA,
  MatSnackBarRef
} from '@angular/material/snack-bar';
import {
  NotificationMessageComponent,
  NotificationMessagePart
} from './notification-message.component';

describe('NotificationMessageComponent', () => {
  let fixture: ComponentFixture<NotificationMessageComponent>;
  let snackBarRef: jasmine.SpyObj<MatSnackBarRef<NotificationMessageComponent>>;

  const parts: NotificationMessagePart[] = [
    'Click the ',
    { icon: 'auto_awesome' },
    ' button.'
  ];

  beforeEach(() => {
    snackBarRef = jasmine.createSpyObj('MatSnackBarRef', ['dismiss']);
    TestBed.configureTestingModule({
      imports: [NotificationMessageComponent],
      providers: [
        { provide: MAT_SNACK_BAR_DATA, useValue: parts },
        { provide: MatSnackBarRef, useValue: snackBarRef }
      ]
    });
    fixture = TestBed.createComponent(NotificationMessageComponent);
    fixture.detectChanges();
  });

  afterEach(() => {
    window.getSelection()?.removeAllRanges();
  });

  it('renders text parts and icon parts in order', () => {
    const label: HTMLElement = fixture.nativeElement.querySelector(
      '.mat-mdc-snack-bar-label'
    );
    const children = Array.from(label.children);

    expect(children.map(child => child.tagName)).toEqual([
      'SPAN',
      'MAT-ICON',
      'SPAN'
    ]);
    expect(label.textContent).toBe('Click the auto_awesome button.');
  });

  it('closes when the message is clicked', () => {
    fixture.nativeElement.querySelector('span').click();

    expect(snackBarRef.dismiss).toHaveBeenCalled();
  });

  it('stays open when the click selected text of the message', () => {
    window.getSelection()?.selectAllChildren(fixture.nativeElement);

    fixture.nativeElement.click();

    expect(snackBarRef.dismiss).not.toHaveBeenCalled();
  });
});
