import { HttpClientTestingModule } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { MatDialog } from '@angular/material/dialog';
import { MockStore, provideMockStore } from '@ngrx/store/testing';
import { IOType } from 'hetida-flowchart';
import { RevisionState } from 'src/app/enums/revision-state';
import { TransformationType } from 'src/app/enums/transformation-type';
import { MaterialModule } from 'src/app/material.module';
import { Transformation } from 'src/app/model/transformation';
import { WorkflowContent } from 'src/app/model/workflow-content';
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
  let transformationHttpService: TransformationHttpService;
  let transformationService: TransformationService;
  let tabItemService: TabItemService;
  let notificationService: NotificationService;
  let mockTransformation: Transformation;
  let mockWorkflowContent: WorkflowContent;
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

    mockWorkflowContent = {
      operators: [
        {
          id: 'mockOperatorId0',
          revision_group_id: 'mockOeratorGroupId0',
          name: 'add',
          type: TransformationType.COMPONENT,
          state: RevisionState.RELEASED,
          version_tag: '1.0.0',
          transformation_id: 'mockOeratorGroupId0',
          inputs: [
            {
              id: 'mockOperatorInputId0',
              name: 'a',
              data_type: IOType.ANY,
              position: {
                x: 0,
                y: 0
              }
            },
            {
              id: 'mockOperatorInputId1',
              name: 'b',
              data_type: IOType.ANY,
              position: {
                x: 0,
                y: 0
              }
            }
          ],
          outputs: [
            {
              id: 'mockOperatorOutputId0',
              name: 'sum',
              data_type: IOType.ANY,
              position: {
                x: 0,
                y: 0
              }
            }
          ],
          position: {
            x: 440,
            y: 315
          }
        }
      ],
      links: [
        {
          id: 'mockLinkId0',
          start: {
            connector: {
              id: 'mockInputId0',
              name: 'mockInput',
              data_type: IOType.ANY,
              position: {
                x: 190,
                y: 375
              }
            }
          },
          end: {
            operator: 'mockOperatorId0',
            connector: {
              id: 'mockOperatorInputId0',
              name: 'a',
              data_type: IOType.ANY,
              position: {
                x: 0,
                y: 0
              }
            }
          },
          path: []
        },
        {
          id: 'mockLinkId1',
          start: {
            operator: 'mockOperatorId0',
            connector: {
              id: 'mockOperatorOutputId0',
              name: 'sum',
              data_type: IOType.ANY,
              position: {
                x: 0,
                y: 0
              }
            }
          },
          end: {
            connector: {
              id: 'mockOutputId0',
              name: 'mockOutput',
              data_type: IOType.ANY,
              position: {
                x: 890,
                y: 375
              }
            }
          },
          path: []
        },
        {
          id: 'mockLinkId2',
          start: {
            connector: {
              id: 'mockConstantId0',
              name: undefined,
              data_type: IOType.ANY,
              position: {
                x: 0,
                y: 0
              }
            }
          },
          end: {
            operator: 'mockOperatorId0',
            connector: {
              id: 'mockOperatorInputId1',
              name: 'b',
              data_type: IOType.ANY,
              position: {
                x: 0,
                y: 0
              }
            }
          },
          path: []
        }
      ],
      inputs: [
        {
          id: 'mockInputId0',
          name: 'mockInput',
          data_type: IOType.ANY,
          operator_id: 'mockOperatorId0',
          connector_id: 'mockOperatorInputId0',
          operator_name: 'add',
          connector_name: 'a',
          position: {
            x: 190,
            y: 375
          }
        }
      ],
      outputs: [
        {
          id: 'mockOutputId0',
          name: 'mockOutput',
          data_type: IOType.ANY,
          operator_id: 'mockOperatorId0',
          connector_id: 'mockOperatorOutputId0',
          operator_name: 'add',
          connector_name: 'sum',
          position: {
            x: 890,
            y: 375
          }
        }
      ],
      constants: [
        {
          id: 'mockConstantId0',
          data_type: IOType.ANY,
          operator_id: 'mockOperatorId0',
          connector_id: 'mockOperatorInputId1',
          operator_name: 'add',
          connector_name: 'b',
          position: {
            x: 0,
            y: 0
          },
          value: '1'
        }
      ]
    };

    TestBed.configureTestingModule({
      imports: [MaterialModule, HttpClientTestingModule],
      providers: [
        provideMockStore(),
        {
          provide: TransformationHttpService,
          useValue: transformationHttpService
        },
        {
          provide: TransformationService,
          useValue: transformationService
        },
        {
          provide: TabItemService,
          useValue: tabItemService
        },
        {
          provide: NotificationService,
          useValue: notificationService
        }
      ]
    });
  });

  beforeEach(() => {
    const matDialog = TestBed.inject(MatDialog);
    const mockStore = TestBed.inject(MockStore);
    transformationHttpService = TestBed.inject(TransformationHttpService);
    transformationService = TestBed.inject(TransformationService);
    tabItemService = TestBed.inject(TabItemService);
    notificationService = TestBed.inject(NotificationService);
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

  it('Copy a transformation from type component', () => {
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

    expect(copyTransformation.io_interface.inputs[0].id).not.toBe(
      'mockInputId0'
    );
    expect(copyTransformation.io_interface.inputs[0].name).toBe('mockInput');
    expect(copyTransformation.io_interface.inputs[0].data_type).toBe(
      IOType.ANY
    );

    expect(copyTransformation.io_interface.outputs[0].id).not.toBe(
      'mockOutputId0'
    );
    expect(copyTransformation.io_interface.outputs[0].name).toBe('mockOutput');
    expect(copyTransformation.io_interface.outputs[0].data_type).toBe(
      IOType.ANY
    );
  });

  it('Copy a transformation from type workflow', () => {
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

    expect(copyTransformation.io_interface.inputs).toHaveSize(0);
    expect(copyTransformation.io_interface.outputs).toHaveSize(0);
  });

  it('Transformation from type component is complete', () => {
    // Act
    const isIncomplete = transformationActionService.isIncomplete(
      mockTransformation
    );
    // Assert
    expect(isIncomplete).toBeFalse();
  });

  it('Transformation from type component is incomplete because io_interface is empty', () => {
    // Arrange
    mockTransformation.io_interface = { inputs: [], outputs: [] };
    // Act
    const isIncomplete = transformationActionService.isIncomplete(
      mockTransformation
    );
    // Assert
    expect(isIncomplete).toBeTrue();
  });

  it('Transformation from type workflow is complete', () => {
    // Arrange
    mockTransformation.content = mockWorkflowContent;
    mockTransformation.type = TransformationType.WORKFLOW;
    // Act
    const isIncomplete = transformationActionService.isIncomplete(
      mockTransformation
    );
    // Assert
    expect(isIncomplete).toBeFalse();
  });

  it('Transformation from type workflow is incomplete because it has no operators', () => {
    // Arrange
    mockTransformation.content = mockWorkflowContent;
    mockTransformation.content.operators = [];
    mockTransformation.type = TransformationType.WORKFLOW;
    // Act
    const isIncomplete = transformationActionService.isIncomplete(
      mockTransformation
    );
    // Assert
    expect(isIncomplete).toBeTrue();
  });

  it('Transformation from type workflow is incomplete because any input name is empty', () => {
    // Arrange
    mockTransformation.content = mockWorkflowContent;
    mockTransformation.content.inputs[0].name = '';
    mockTransformation.type = TransformationType.WORKFLOW;
    // Act
    const isIncomplete = transformationActionService.isIncomplete(
      mockTransformation
    );
    // Assert
    expect(isIncomplete).toBeTrue();
  });

  it('Transformation from type workflow is incomplete because any output name is empty', () => {
    // Arrange
    mockTransformation.content = mockWorkflowContent;
    mockTransformation.content.outputs[0].name = '';
    mockTransformation.type = TransformationType.WORKFLOW;
    // Act
    const isIncomplete = transformationActionService.isIncomplete(
      mockTransformation
    );
    // Assert
    expect(isIncomplete).toBeTrue();
  });

  it('Transformation from type workflow is incomplete because any input name is not a valid python identifier', () => {
    // Arrange
    mockTransformation.content = mockWorkflowContent;
    mockTransformation.content.inputs[0].name = '0input';
    mockTransformation.type = TransformationType.WORKFLOW;
    // Act
    const isIncomplete = transformationActionService.isIncomplete(
      mockTransformation
    );
    // Assert
    expect(isIncomplete).toBeTrue();
  });

  it('Transformation from type workflow is incomplete because any output name is not a valid python identifier', () => {
    // Arrange
    mockTransformation.content = mockWorkflowContent;
    mockTransformation.content.outputs[0].name = '0output';
    mockTransformation.type = TransformationType.WORKFLOW;
    // Act
    const isIncomplete = transformationActionService.isIncomplete(
      mockTransformation
    );
    // Assert
    expect(isIncomplete).toBeTrue();
  });

  it('Transformation from type workflow is incomplete because any input name is a python keyword', () => {
    // Arrange
    mockTransformation.content = mockWorkflowContent;
    mockTransformation.content.inputs[0].name = 'break';
    mockTransformation.type = TransformationType.WORKFLOW;
    // Act
    const isIncomplete = transformationActionService.isIncomplete(
      mockTransformation
    );
    // Assert
    expect(isIncomplete).toBeTrue();
  });

  it('Transformation from type workflow is incomplete because any output name is a python keyword', () => {
    // Arrange
    mockTransformation.content = mockWorkflowContent;
    mockTransformation.content.outputs[0].name = 'break';
    mockTransformation.type = TransformationType.WORKFLOW;
    // Act
    const isIncomplete = transformationActionService.isIncomplete(
      mockTransformation
    );
    // Assert
    expect(isIncomplete).toBeTrue();
  });

  it('Transformation from type workflow is incomplete because there is not a link from every input', () => {
    // Arrange
    mockTransformation.content = mockWorkflowContent;
    mockTransformation.content.links = mockTransformation.content.links.filter(
      link => link.id !== 'mockLinkId0'
    );
    mockTransformation.type = TransformationType.WORKFLOW;
    // Act
    const isIncomplete = transformationActionService.isIncomplete(
      mockTransformation
    );
    // Assert
    expect(isIncomplete).toBeTrue();
  });

  it('Transformation from type workflow is incomplete because there is not a link to every output', () => {
    // Arrange
    mockTransformation.content = mockWorkflowContent;
    mockTransformation.content.links = mockTransformation.content.links.filter(
      link => link.id !== 'mockLinkId1'
    );
    mockTransformation.type = TransformationType.WORKFLOW;
    // Act
    const isIncomplete = transformationActionService.isIncomplete(
      mockTransformation
    );
    // Assert
    expect(isIncomplete).toBeTrue();
  });
});
