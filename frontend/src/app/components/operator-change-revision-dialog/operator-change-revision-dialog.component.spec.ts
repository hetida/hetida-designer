import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';
import { MatOptionModule } from '@angular/material/core';
import { MatDialogRef, MAT_DIALOG_DATA } from '@angular/material/dialog';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatSelectModule } from '@angular/material/select';
import { BrowserAnimationsModule } from '@angular/platform-browser/animations';
import { OperatorChangeRevisionDialogComponent } from './operator-change-revision-dialog.component';

describe('OperatorChangeRevisionDialogComponent', () => {
  let component: OperatorChangeRevisionDialogComponent;
  let fixture: ComponentFixture<OperatorChangeRevisionDialogComponent>;

  beforeEach(
    waitForAsync(() => {
      TestBed.configureTestingModule({
        imports: [
          MatFormFieldModule,
          MatSelectModule,
          MatOptionModule,
          BrowserAnimationsModule
        ],
        declarations: [OperatorChangeRevisionDialogComponent],
        providers: [
          { provide: MatDialogRef, useValue: {} },
          {
            provide: MAT_DIALOG_DATA,
            useValue: {}
          }
        ]
      }).compileComponents();
    })
  );

  beforeEach(() => {
    fixture = TestBed.createComponent(OperatorChangeRevisionDialogComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
