import { ComponentFixture, TestBed } from '@angular/core/testing';

import { OptionalFieldsDialogComponent } from './optional-fields-dialog.component';

describe('OptionalFieldsDialogComponent', () => {
  let component: OptionalFieldsDialogComponent;
  let fixture: ComponentFixture<OptionalFieldsDialogComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [OptionalFieldsDialogComponent]
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
