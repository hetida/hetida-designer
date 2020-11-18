import { HttpClientModule } from '@angular/common/http';
import { async, ComponentFixture, TestBed } from '@angular/core/testing';
import { FormsModule, ReactiveFormsModule } from '@angular/forms';
import { MatDialogRef, MAT_DIALOG_DATA } from '@angular/material/dialog';
import { StoreModule } from '@ngrx/store';
import { BasicTestModule } from 'src/app/angular-test.module';
import { BaseItemType } from 'src/app/enums/base-item-type';
import { appReducers } from 'src/app/store/app.reducers';
import { ExecutionDialogComponent } from './execution-dialog.component';

describe('ExecutionDialogComponent', () => {
  let component: ExecutionDialogComponent;
  let fixture: ComponentFixture<ExecutionDialogComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      imports: [
        BasicTestModule,
        FormsModule,
        ReactiveFormsModule,
        HttpClientModule,
        StoreModule.forRoot(appReducers)
      ],
      declarations: [ExecutionDialogComponent],
      providers: [
        { provide: MatDialogRef, useValue: {} },
        {
          provide: MAT_DIALOG_DATA,
          useValue: {
            abstractBaseItem: {
              id: 'Mock',
              name: 'Mock',
              tag: 'Mock',
              pos_x: null,
              pos_y: null,
              inputs: [],
              outputs: [],
              links: [],
              type: BaseItemType.COMPONENT
            }
          }
        }
      ]
    }).compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(ExecutionDialogComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
