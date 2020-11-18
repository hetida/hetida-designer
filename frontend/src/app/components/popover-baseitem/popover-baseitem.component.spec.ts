import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { PopoverBaseitemComponent } from './popover-baseitem.component';
import { MatAutocompleteModule } from '@angular/material/autocomplete';
import { MatDividerModule } from '@angular/material/divider';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatIconModule } from '@angular/material/icon';
import { NgHetidaFlowchartModule } from 'ng-hetida-flowchart';
import { FormsModule, ReactiveFormsModule } from '@angular/forms';
import { StoreModule } from '@ngrx/store';
import { appReducers } from 'src/app/store/app.reducers';
import { HttpClientModule } from '@angular/common/http';

describe('PopoverBaseitemComponent', () => {
  let component: PopoverBaseitemComponent;
  let fixture: ComponentFixture<PopoverBaseitemComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      imports: [
        MatIconModule,
        NgHetidaFlowchartModule,
        MatDividerModule,
        MatFormFieldModule,
        FormsModule,
        ReactiveFormsModule,
        MatAutocompleteModule,
        StoreModule.forRoot(appReducers),
        HttpClientModule
      ],
      declarations: [PopoverBaseitemComponent]
    }).compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(PopoverBaseitemComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
