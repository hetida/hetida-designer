import {
  provideHttpClient,
  withInterceptorsFromDi
} from '@angular/common/http';
import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';
import { FormsModule, ReactiveFormsModule } from '@angular/forms';
import { MatAutocompleteModule } from '@angular/material/autocomplete';
import { MatDividerModule } from '@angular/material/divider';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatIconModule } from '@angular/material/icon';
import { StoreModule } from '@ngrx/store';
import { NgHetidaFlowchartModule } from 'ng-hetida-flowchart';
import { appReducers } from 'src/app/store/app.reducers';
import { PopoverTransformationComponent } from './popover-transformation.component';
import { RouterModule } from '@angular/router';

describe('PopoverTransformationComponent', () => {
  let component: PopoverTransformationComponent;
  let fixture: ComponentFixture<PopoverTransformationComponent>;

  beforeEach(waitForAsync(() => {
    TestBed.configureTestingModule({
      declarations: [PopoverTransformationComponent],
      imports: [
        MatIconModule,
        NgHetidaFlowchartModule,
        MatDividerModule,
        MatFormFieldModule,
        FormsModule,
        ReactiveFormsModule,
        MatAutocompleteModule,
        StoreModule.forRoot(appReducers),
        RouterModule.forRoot([])
      ],
      providers: [provideHttpClient(withInterceptorsFromDi())]
    }).compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(PopoverTransformationComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
