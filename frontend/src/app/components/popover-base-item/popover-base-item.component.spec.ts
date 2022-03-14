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
import { PopoverBaseItemComponent } from './popover-base-item.component';

describe('PopoverBaseItemComponent', () => {
  let component: PopoverBaseItemComponent;
  let fixture: ComponentFixture<PopoverBaseItemComponent>;

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
        declarations: [PopoverBaseItemComponent]
      }).compileComponents();
    })
  );

  beforeEach(() => {
    fixture = TestBed.createComponent(PopoverBaseItemComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
