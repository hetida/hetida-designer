import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';
import { FormsModule, ReactiveFormsModule } from '@angular/forms';
import { MatDialogRef, MAT_DIALOG_DATA } from '@angular/material/dialog';
import { NgHetidaFlowchartModule } from 'ng-hetida-flowchart';
import { ErrorVisualDirective } from 'src/app/directives/error-visual.directive';
import { BaseItemType } from 'src/app/enums/base-item-type';
import { MaterialModule } from 'src/app/material.module';
import { WorkflowIODialogComponent } from './workflow-io-dialog.component';

describe('WorkflowIODialogComponent', () => {
  let component: WorkflowIODialogComponent;
  let fixture: ComponentFixture<WorkflowIODialogComponent>;

  beforeEach(
    waitForAsync(() => {
      TestBed.configureTestingModule({
        imports: [
          FormsModule,
          ReactiveFormsModule,
          MaterialModule,
          NgHetidaFlowchartModule
        ],
        declarations: [WorkflowIODialogComponent, ErrorVisualDirective],
        providers: [
          { provide: MatDialogRef, useValue: {} },
          {
            provide: MAT_DIALOG_DATA,
            useValue: {
              workflow: {
                operators: [],
                links: [],
                id: 'Mock',
                groupId: 'Mock',
                name: 'Mock',
                description: 'Mock',
                category: 'Mock',
                type: BaseItemType.WORKFLOW,
                tag: 'Mock',
                state: 'DRAFT',
                inputs: [],
                outputs: []
              }
            }
          }
        ]
      }).compileComponents();
    })
  );

  beforeEach(() => {
    fixture = TestBed.createComponent(WorkflowIODialogComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
