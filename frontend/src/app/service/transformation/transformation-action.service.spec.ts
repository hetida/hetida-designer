import { HttpClientTestingModule } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { MatDialog } from '@angular/material/dialog';
import { MockStore, provideMockStore } from '@ngrx/store/testing';
import { IOType, IOTypeOption } from 'hetida-flowchart';
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
import { QueryParameterService } from '../query-parameter/query-parameter.service';
import { RouterTestingModule } from '@angular/router/testing';

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
            data_type: IOType.ANY,
            type: IOTypeOption.REQUIRED
          }
        ],
        outputs: [
          {
            id: 'mockOutputId0',
            name: 'mockOutput',
            data_type: IOType.ANY,
            type: IOTypeOption.REQUIRED
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
          },
          type: IOTypeOption.REQUIRED
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
          },
          type: IOTypeOption.REQUIRED
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
          value: '1',
          type: IOTypeOption.REQUIRED
        }
      ]
    };

    transformationHttpServiceSpy = jasmine.createSpy();
    transformationServiceSpy = jasmine.createSpy();
    tabItemServiceSpy = jasmine.createSpy();
    notificationServiceSpy = jasmine.createSpy();

    TestBed.configureTestingModule({
      imports: [MaterialModule, HttpClientTestingModule, RouterTestingModule],
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
    const queryParameterService = TestBed.inject(QueryParameterService);
    transformationActionService = new TransformationActionServiceExtended(
      matDialog,
      mockStore,
      transformationHttpService,
      transformationService,
      tabItemService,
      notificationService,
      queryParameterService
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
        'Inputs in io_interface should be empty because they are regenerated in the backend'
      )
      .toHaveSize(0);
    expect(copyTransformation.io_interface.outputs)
      .withContext(
        'Outputs in io_interface should be empty because they are regenerated in the backend'
      )
      .toHaveSize(0);
  });

  it('IsIncomplete should return false if component fulfills all requirements', () => {
    // Act
    const isIncomplete =
      transformationActionService.isIncomplete(mockTransformation);
    // Assert
    expect(isIncomplete).toBeFalse();
  });

  it('IsIncomplete should return true if io_interface is empty', () => {
    // Arrange
    mockTransformation.io_interface = { inputs: [], outputs: [] };
    // Act
    const isIncomplete =
      transformationActionService.isIncomplete(mockTransformation);
    // Assert
    expect(isIncomplete).toBeTrue();
  });

  it('IsIncomplete should return false if workflow fulfills all requirements', () => {
    // Arrange
    mockTransformation.content = mockWorkflowContent;
    mockTransformation.type = TransformationType.WORKFLOW;
    // Act
    const isIncomplete =
      transformationActionService.isIncomplete(mockTransformation);
    // Assert
    expect(isIncomplete).toBeFalse();
  });

  it('IsIncomplete should return false if workflow has no operators', () => {
    // Arrange
    mockTransformation.content = mockWorkflowContent;
    mockTransformation.content.operators = [];
    mockTransformation.type = TransformationType.WORKFLOW;
    // Act
    const isIncomplete =
      transformationActionService.isIncomplete(mockTransformation);
    // Assert
    expect(isIncomplete).toBeTrue();
  });

  it('IsIncomplete should return false if any workflow input name is empty', () => {
    // Arrange
    mockTransformation.content = mockWorkflowContent;
    mockTransformation.content.inputs[0].name = '';
    mockTransformation.type = TransformationType.WORKFLOW;
    // Act
    const isIncomplete =
      transformationActionService.isIncomplete(mockTransformation);
    // Assert
    expect(isIncomplete).toBe(false);
  });

  it('IsIncomplete should return false if any workflow output name is empty', () => {
    // Arrange
    mockTransformation.content = mockWorkflowContent;
    mockTransformation.content.outputs[0].name = '';
    mockTransformation.type = TransformationType.WORKFLOW;
    // Act
    const isIncomplete =
      transformationActionService.isIncomplete(mockTransformation);
    // Assert
    expect(isIncomplete).toBeTrue();
  });

  it('IsIncomplete should return false if any workflow input name is not a valid python identifier', () => {
    // Arrange
    mockTransformation.content = mockWorkflowContent;
    mockTransformation.content.inputs[0].name = '0input';
    mockTransformation.type = TransformationType.WORKFLOW;
    // Act
    const isIncomplete =
      transformationActionService.isIncomplete(mockTransformation);
    // Assert
    expect(isIncomplete).toBe(false);
  });

  it('IsIncomplete should return true if any workflow output name is not a valid python identifier', () => {
    // Arrange
    mockTransformation.content = mockWorkflowContent;
    mockTransformation.content.outputs[0].name = '0output';
    mockTransformation.type = TransformationType.WORKFLOW;
    // Act
    const isIncomplete =
      transformationActionService.isIncomplete(mockTransformation);
    // Assert
    expect(isIncomplete).toBe(true);
  });

  it('IsIncomplete should return false if any workflow input name is a python keyword', () => {
    // Arrange
    mockTransformation.content = mockWorkflowContent;
    mockTransformation.content.inputs[0].name = 'break';
    mockTransformation.type = TransformationType.WORKFLOW;
    // Act
    const isIncomplete =
      transformationActionService.isIncomplete(mockTransformation);
    // Assert
    expect(isIncomplete).toBe(false);
  });

  it('IsIncomplete should return false if any workflow output name is a python keyword', () => {
    // Arrange
    mockTransformation.content = mockWorkflowContent;
    mockTransformation.content.outputs[0].name = 'break';
    mockTransformation.type = TransformationType.WORKFLOW;
    // Act
    const isIncomplete =
      transformationActionService.isIncomplete(mockTransformation);
    // Assert
    expect(isIncomplete).toBeTrue();
  });

  it('IsIncomplete should return false if workflow does not have a link from every input', () => {
    // Arrange
    mockTransformation.content = mockWorkflowContent;
    mockTransformation.content.links = mockTransformation.content.links.filter(
      link => link.id !== 'mockLinkId0'
    );
    mockTransformation.type = TransformationType.WORKFLOW;
    // Act
    const isIncomplete =
      transformationActionService.isIncomplete(mockTransformation);
    // Assert
    expect(isIncomplete).toBe(false);
  });

  it('IsIncomplete should return false if workflow does not have a link to every output', () => {
    // Arrange
    mockTransformation.content = mockWorkflowContent;
    mockTransformation.content.links = mockTransformation.content.links.filter(
      link => link.id !== 'mockLinkId1'
    );
    mockTransformation.type = TransformationType.WORKFLOW;
    // Act
    const isIncomplete =
      transformationActionService.isIncomplete(mockTransformation);
    // Assert
    expect(isIncomplete).toBeTrue();
  });
});
