import { ComponentFixture, TestBed } from '@angular/core/testing';

import { OptionalFieldsDialogComponent } from './optional-fields-dialog.component';
import { provideMockStore } from '@ngrx/store/testing';
import { MAT_DIALOG_DATA, MatDialogRef } from '@angular/material/dialog';
import { ReactiveFormsModule } from '@angular/forms';
import { MatIconModule } from '@angular/material/icon';

describe('OptionalFieldsDialogComponent', () => {
  let component: OptionalFieldsDialogComponent;
  let fixture: ComponentFixture<OptionalFieldsDialogComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [ReactiveFormsModule, MatIconModule],
      declarations: [OptionalFieldsDialogComponent],
      providers: [
        provideMockStore(),
        {
          provide: MatDialogRef,
          useValue: {}
        },
        {
          provide: MAT_DIALOG_DATA,
          useValue: {
            operator: {
              inputs: []
            },
            actionOk: 'ok',
            actionCancel: 'cancel'
          }
        }
      ]
    }).compileComponents();
  });

  beforeEach(() => {
    fixture = TestBed.createComponent(OptionalFieldsDialogComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
