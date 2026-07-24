import { ComponentFixture, TestBed } from '@angular/core/testing';
import { WarningDialogComponent } from './warning-dialog.component';
import { MAT_DIALOG_DATA } from '@angular/material/dialog';
import { MaterialModule } from '../material.module';

describe('WarningDialogComponent', () => {
  let component: WarningDialogComponent;
  let fixture: ComponentFixture<WarningDialogComponent>;

  beforeEach(async () => {
    const warningDialogData = {
      data: 'Test Warning'
    };

    await TestBed.configureTestingModule({
      imports: [MaterialModule],
      declarations: [WarningDialogComponent],
      providers: [
        {
          provide: MAT_DIALOG_DATA,
          useValue: warningDialogData
        }
      ]
    }).compileComponents();
  });

  beforeEach(() => {
    fixture = TestBed.createComponent(WarningDialogComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
