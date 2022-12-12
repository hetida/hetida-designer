import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';
import { FormsModule, ReactiveFormsModule } from '@angular/forms';
import { MatDialogRef, MAT_DIALOG_DATA } from '@angular/material/dialog';
import { NgHetidaFlowchartModule } from 'ng-hetida-flowchart';
import { ErrorVisualDirective } from 'src/app/directives/error-visual.directive';
import { BaseItemType } from 'src/app/enums/base-item-type';
import { RevisionState } from 'src/app/enums/revision-state';
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
              workflowTransformation: {
                id: 'mockId0',
                revision_group_id: 'mockGroupId',
                name: 'Mock',
                description: 'mock description',
                category: 'EXAMPLES',
                version_tag: '0.0.1',
                released_timestamp: new Date().toISOString(),
                disabled_timestamp: new Date().toISOString(),
                state: RevisionState.DRAFT,
                type: BaseItemType.WORKFLOW,
                documentation: null,
                content: {
                  operators: [],
                  links: [],
                  inputs: [],
                  outputs: [],
                  constants: []
                },
                io_interface: {
                  inputs: [],
                  outputs: []
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
