import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';
import { NoopAnimationsModule } from '@angular/platform-browser/animations';
import { Subject } from 'rxjs';
import { TransformationType } from 'src/app/enums/transformation-type';
import { RevisionState } from 'src/app/enums/revision-state';
import { MaterialModule } from 'src/app/material.module';
import {
  Transformation,
  WorkflowTransformation
} from 'src/app/model/transformation';
import { TransformationActionService } from 'src/app/service/transformation/transformation-action.service';
import { TransformationService } from 'src/app/service/transformation/transformation.service';
import { TabItemService } from 'src/app/service/tab-item/tab-item.service';
import { TransformationContextMenuComponent } from './transformation-context-menu.component';

describe('TransformationContextMenuComponent', () => {
  let component: TransformationContextMenuComponent;
  let fixture: ComponentFixture<TransformationContextMenuComponent>;
  let transformationActionService: jasmine.SpyObj<TransformationActionService>;
  let transformationService: jasmine.SpyObj<TransformationService>;

  beforeEach(waitForAsync(() => {
    transformationActionService =
      jasmine.createSpyObj<TransformationActionService>(
        'TransformationActionService',
        ['isIncomplete', 'isWorkflowWithoutIo']
      );

    transformationService = jasmine.createSpyObj<TransformationService>(
      'TransformationService',
      ['getFullTransformation']
    );

    const tabItemService = jasmine.createSpyObj<TabItemService>(
      'TabItemService',
      ['addTransformationTab']
    );

    TestBed.configureTestingModule({
      imports: [MaterialModule, NoopAnimationsModule],
      declarations: [TransformationContextMenuComponent],
      providers: [
        {
          provide: TransformationActionService,
          useValue: transformationActionService
        },
        {
          provide: TransformationService,
          useValue: transformationService
        },
        {
          provide: TabItemService,
          useValue: tabItemService
        }
      ]
    }).compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(TransformationContextMenuComponent);
    component = fixture.componentInstance;
    component.transformation = {
      id: 'mockId',
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
        inputs: [],
        outputs: []
      },
      test_wiring: {
        input_wirings: [],
        output_wirings: []
      }
    };
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should be not published', () => {
    expect(component._isNotPublished).toBe(true);
  });

  it('should hide content dependent entries of a stub until it is fully loaded', () => {
    const fullWorkflow: WorkflowTransformation = {
      id: 'mockWorkflowId',
      revision_group_id: 'mockWorkflowGroupId',
      name: 'mock workflow',
      category: 'EXAMPLES',
      version_tag: '0.0.1',
      state: RevisionState.RELEASED,
      type: TransformationType.WORKFLOW,
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
    };
    const workflowStub = {
      ...fullWorkflow,
      content: undefined,
      test_wiring: undefined
    } as Transformation;
    const loadedWorkflow = new Subject<Transformation>();
    transformationService.getFullTransformation.and.returnValue(loadedWorkflow);
    transformationActionService.isIncomplete.and.returnValue(false);
    transformationActionService.isWorkflowWithoutIo.and.returnValue(false);

    component.transformation = workflowStub;

    expect(transformationService.getFullTransformation).toHaveBeenCalledWith(
      'mockWorkflowId'
    );
    expect(component._isIncomplete).toBe(true);
    expect(component._isWorkflowWithoutIo).toBe(true);
    expect(component._isNotPublished).toBe(false);

    loadedWorkflow.next(fullWorkflow);

    expect(component.transformation).toBe(fullWorkflow);
    expect(transformationActionService.isIncomplete).toHaveBeenCalledWith(
      fullWorkflow
    );
    expect(component._isIncomplete).toBe(false);
    expect(component._isWorkflowWithoutIo).toBe(false);
  });
});
