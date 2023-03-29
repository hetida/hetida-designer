import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';
import { FormsModule, ReactiveFormsModule } from '@angular/forms';
import { MAT_DIALOG_DATA, MatDialogRef } from '@angular/material/dialog';
import { IOType } from 'hetida-flowchart';
import { NgHetidaFlowchartModule } from 'ng-hetida-flowchart';
import { BasicTestModule } from 'src/app/basic-test.module';
import { ErrorVisualDirective } from 'src/app/directives/error-visual.directive';
import { RevisionState } from 'src/app/enums/revision-state';
import { TransformationType } from 'src/app/enums/transformation-type';
import { ComponentIODialogComponent } from './component-io-dialog.component';

describe('ComponentIODialogComponent', () => {
  let component: ComponentIODialogComponent;
  let fixture: ComponentFixture<ComponentIODialogComponent>;

  beforeEach(
    waitForAsync(() => {
      TestBed.configureTestingModule({
        imports: [
          BasicTestModule,
          FormsModule,
          ReactiveFormsModule,
          NgHetidaFlowchartModule
        ],
        declarations: [ComponentIODialogComponent, ErrorVisualDirective],
        providers: [
          { provide: MatDialogRef, useValue: {} },
          {
            provide: MAT_DIALOG_DATA,
            useValue: {
              componentTransformation: {
                id: 'mockId0',
                revision_group_id: 'mockGroupId',
                name: 'mock',
                description: 'mock description',
                category: 'EXAMPLES',
                version_tag: '0.0.1',
                released_timestamp: new Date().toISOString(),
                disabled_timestamp: new Date().toISOString(),
                state: RevisionState.DRAFT,
                type: TransformationType.COMPONENT,
                documentation: null,
                content: 'python code',
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
              },
              editMode: true
            }
          }
        ]
      }).compileComponents();
    })
  );

  beforeEach(() => {
    fixture = TestBed.createComponent(ComponentIODialogComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
