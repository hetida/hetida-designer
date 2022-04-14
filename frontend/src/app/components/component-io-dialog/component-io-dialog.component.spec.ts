import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';
import { FormsModule, ReactiveFormsModule } from '@angular/forms';
import { MAT_DIALOG_DATA, MatDialogRef } from '@angular/material/dialog';
import { NgHetidaFlowchartModule } from 'ng-hetida-flowchart';
import { BasicTestModule } from 'src/app/basic-test.module';
import { ErrorVisualDirective } from 'src/app/directives/error-visual.directive';
import { BaseItemType } from 'src/app/enums/base-item-type';
import { ComponentIODialogComponent } from './component-io-dialog.component';

describe('ComponentIODialogComponent', () => {
  let component: ComponentIODialogComponent;
  let fixture: ComponentFixture<ComponentIODialogComponent>;

  beforeEach(waitForAsync(() => {
    TestBed.configureTestingModule({
      imports: [
        BasicTestModule,
        NgHetidaFlowchartModule,
        FormsModule,
        ReactiveFormsModule
      ],
      declarations: [ComponentIODialogComponent, ErrorVisualDirective],
      providers: [
        {
          provide: MAT_DIALOG_DATA,
          useValue: {
            componentBaseItem: {
              id: 'Mock',
              name: 'Mock',
              tag: 'Mock',
              pos_x: null,
              pos_y: null,
              inputs: [],
              outputs: [],
              links: [],
              type: BaseItemType.COMPONENT
            },
            editMode: true
          }
        },
        { provide: MatDialogRef, useValue: {} }
      ]
    }).compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(ComponentIODialogComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
