import { Component, Input } from '@angular/core';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import {
  FormControl,
  FormGroup,
  ReactiveFormsModule,
  Validators
} from '@angular/forms';
import { ErrorVisualDirective } from './error-visual.directive';

describe('ErrorVisualDirective', () => {
  let fixture: ComponentFixture<TestComponent>;

  @Component({
    template: ` <form [formGroup]="formGroup">
      <input formControlName="name" matInput type="text" />
      <mat-error id="error" [hdErrorVisual]="formGroup.get('name')"></mat-error>
    </form>`
  })
  class TestComponent {
    @Input()
    public formGroup: FormGroup;
  }

  beforeEach(() => {
    TestBed.configureTestingModule({
      declarations: [TestComponent, ErrorVisualDirective],
      imports: [ReactiveFormsModule]
    });
    fixture = TestBed.createComponent(TestComponent);
  });

  it('should be invisible if form control is valid', () => {
    fixture.componentInstance.formGroup = new FormGroup({
      name: new FormControl('valid name', Validators.required)
    });
    fixture.detectChanges();
    const errorElement: HTMLElement =
      fixture.debugElement.nativeElement.querySelector('#error');
    expect(errorElement.style.visibility).toBe('');
  });

  it('should be visible if form control is invalid', () => {
    fixture.componentInstance.formGroup = new FormGroup({
      name: new FormControl('', Validators.required)
    });
    fixture.detectChanges();
    const errorElement: HTMLElement =
      fixture.debugElement.nativeElement.querySelector('#error');
    expect(errorElement.style.visibility).toBe('visible');
  });

  it('should show error text if form control is invalid', () => {
    fixture.componentInstance.formGroup = new FormGroup({
      name: new FormControl('', Validators.required)
    });
    fixture.detectChanges();
    const errorElement: HTMLElement =
      fixture.debugElement.nativeElement.querySelector('#error');
    expect(errorElement.innerText).toBe('Cannot be empty');
  });
});
