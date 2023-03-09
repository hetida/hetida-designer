import { HttpClientTestingModule } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { MatDialog } from '@angular/material/dialog';
import { MockStore, provideMockStore } from '@ngrx/store/testing';
import { IOType } from 'hetida-flowchart';
import { RevisionState } from 'src/app/enums/revision-state';
import { TransformationType } from 'src/app/enums/transformation-type';
import { MaterialModule } from 'src/app/material.module';
import { Transformation } from 'src/app/model/transformation';
import { TransformationHttpService } from '../http-service/transformation-http.service';
import { NotificationService } from '../notifications/notification.service';
import { TabItemService } from '../tab-item/tab-item.service';
import { TransformationActionService } from './transformation-action.service';
import { TransformationService } from './transformation.service';

class TransformationActionServiceExtended extends TransformationActionService {
  public copyTransformation(
    newId: string,
    groupId: string,
    suffix: string,
    transformation: Transformation
  ): Transformation {
    return super.copyTransformation(newId, groupId, suffix, transformation);
  }
}

describe('TransformationActionService', () => {
  let transformationHttpServiceSpy;
  let transformationServiceSpy;
  let tabItemServiceSpy;
  let notificationServiceSpy;
  let mockTransformation: Transformation;
  let transformationActionService: TransformationActionServiceExtended;

  beforeEach(() => {
    mockTransformation = {
      id: 'mockId0',
      revision_group_id: 'mockGroupId0',
      name: 'sum',
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
            id: 'mockInputId0',
            name: 'mockInput',
            data_type: IOType.ANY
          }
        ],
        outputs: [
          {
            id: 'mockOutputId0',
            name: 'mockOutput',
            data_type: IOType.ANY
          }
        ]
      },
      test_wiring: {
        input_wirings: [],
        output_wirings: []
      }
    };

    transformationHttpServiceSpy = jasmine.createSpy();
    transformationServiceSpy = jasmine.createSpy();
    tabItemServiceSpy = jasmine.createSpy();
    notificationServiceSpy = jasmine.createSpy();

    TestBed.configureTestingModule({
      imports: [MaterialModule, HttpClientTestingModule],
      providers: [
        provideMockStore(),
        {
          provide: TransformationHttpService,
          useValue: transformationHttpServiceSpy
        },
        {
          provide: TransformationService,
          useValue: transformationServiceSpy
        },
        {
          provide: TabItemService,
          useValue: tabItemServiceSpy
        },
        {
          provide: NotificationService,
          useValue: notificationServiceSpy
        }
      ]
    });
  });

  beforeEach(() => {
    const matDialog = TestBed.inject(MatDialog);
    const mockStore = TestBed.inject(MockStore);
    const transformationHttpService = TestBed.inject(TransformationHttpService);
    const transformationService = TestBed.inject(TransformationService);
    const tabItemService = TestBed.inject(TabItemService);
    const notificationService = TestBed.inject(NotificationService);
    transformationActionService = new TransformationActionServiceExtended(
      matDialog,
      mockStore,
      transformationHttpService,
      transformationService,
      tabItemService,
      notificationService
    );
  });

  it('TransformationActionService should be created', () => {
    // Assert
    expect(transformationActionService).toBeTruthy();
  });

  it('Copy transformation should copy components correctly', () => {
    // Arrange
    const mockNewId = 'mockId1';
    const mockGroupId = 'mockGroupId1';
    const mockSuffix = 'Copy';
    // Act
    const copyTransformation = transformationActionService.copyTransformation(
      mockNewId,
      mockGroupId,
      mockSuffix,
      mockTransformation
    );
    // Assert
    expect(copyTransformation.id).toBe('mockId1');
    expect(copyTransformation.revision_group_id).toBe('mockGroupId1');
    expect(copyTransformation.version_tag).toBe('0.0.1 Copy');
    expect(copyTransformation.state).toBe(RevisionState.DRAFT);

    expect(copyTransformation.io_interface.inputs[0].id)
      .withContext('Inputs should get new generated ids')
      .not.toBe('mockInputId0');
    expect(copyTransformation.io_interface.inputs[0].name).toBe('mockInput');
    expect(copyTransformation.io_interface.inputs[0].data_type).toBe(
      IOType.ANY
    );

    expect(copyTransformation.io_interface.outputs[0].id)
      .withContext('Outputs should get new generated ids')
      .not.toBe('mockOutputId0');
    expect(copyTransformation.io_interface.outputs[0].name).toBe('mockOutput');
    expect(copyTransformation.io_interface.outputs[0].data_type).toBe(
      IOType.ANY
    );
  });

  it('Copy transformation should copy workflows correctly', () => {
    // Arrange
    const mockNewId = 'mockId1';
    const mockGroupId = 'mockGroupId1';
    const mockSuffix = 'Copy';
    mockTransformation.type = TransformationType.WORKFLOW;
    // Act
    const copyTransformation = transformationActionService.copyTransformation(
      mockNewId,
      mockGroupId,
      mockSuffix,
      mockTransformation
    );
    // Assert
    expect(copyTransformation.id).toBe('mockId1');
    expect(copyTransformation.revision_group_id).toBe('mockGroupId1');
    expect(copyTransformation.version_tag).toBe('0.0.1 Copy');
    expect(copyTransformation.state).toBe(RevisionState.DRAFT);

    expect(copyTransformation.io_interface.inputs)
      .withContext(
        'Inputs in io-interface should be empty because they are regenerated in the backend'
      )
      .toHaveSize(0);
    expect(copyTransformation.io_interface.outputs)
      .withContext(
        'Outputs in io-interface should be empty because they are regenerated in the backend'
      )
      .toHaveSize(0);
  });
});
