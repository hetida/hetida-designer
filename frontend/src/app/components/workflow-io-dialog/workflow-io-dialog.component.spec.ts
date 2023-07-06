import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';
import { FormsModule, ReactiveFormsModule } from '@angular/forms';
import { MatDialogRef, MAT_DIALOG_DATA } from '@angular/material/dialog';
import { ErrorVisualDirective } from 'src/app/directives/error-visual.directive';
import { TransformationType } from 'src/app/enums/transformation-type';
import { RevisionState } from 'src/app/enums/revision-state';
import { MaterialModule } from 'src/app/material.module';
import { WorkflowIODialogComponent } from './workflow-io-dialog.component';
import { IOType } from 'hetida-flowchart';
import { NgHetidaFlowchartModule } from 'ng-hetida-flowchart';

describe('WorkflowIODialogComponent', () => {
  let component: WorkflowIODialogComponent;
  let fixture: ComponentFixture<WorkflowIODialogComponent>;

  beforeEach(waitForAsync(() => {
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
            workflowTransformation: {
              id: 'mockId',
              revision_group_id: 'mockGroupId',
              name: 'mock',
              description: 'mock description',
              category: 'EXAMPLES',
              version_tag: '0.0.1',
              released_timestamp: new Date().toISOString(),
              disabled_timestamp: new Date().toISOString(),
              state: RevisionState.DRAFT,
              type: TransformationType.WORKFLOW,
              documentation: null,
              content: {
                operators: [],
                links: [],
                inputs: [],
                outputs: [],
                constants: []
              },
              io_interface: {
                inputs: [
                  {
                    id: 'mockId0',
                    name: 'mockInput',
                    data_type: IOType.ANY
                  }
                ],
                outputs: [
                  {
                    id: 'mockId0',
                    name: 'mockInput',
                    data_type: IOType.ANY
                  }
                ]
              },
              test_wiring: {
                input_wirings: [],
                output_wirings: []
              }
            }
          }
        }
      ]
    }).compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(WorkflowIODialogComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
