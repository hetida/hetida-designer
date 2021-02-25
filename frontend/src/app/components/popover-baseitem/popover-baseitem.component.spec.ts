import { HttpClientModule } from '@angular/common/http';
import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';
import { FormsModule, ReactiveFormsModule } from '@angular/forms';
import { MatAutocompleteModule } from '@angular/material/autocomplete';
import { MatDividerModule } from '@angular/material/divider';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatIconModule } from '@angular/material/icon';
import { StoreModule } from '@ngrx/store';
import { NgHetidaFlowchartModule } from 'ng-hetida-flowchart';
import { appReducers } from 'src/app/store/app.reducers';
import { PopoverBaseitemComponent } from './popover-baseitem.component';

describe('PopoverBaseitemComponent', () => {
  let component: PopoverBaseitemComponent;
  let fixture: ComponentFixture<PopoverBaseitemComponent>;

  beforeEach(
    waitForAsync(() => {
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
    })
  );

  beforeEach(() => {
    fixture = TestBed.createComponent(PopoverBaseitemComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
