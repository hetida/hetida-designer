import {
  selectAllTransformations,
  selectHashedTransformationLookupById,
  selectTransformationById,
  selectTransformationsByCategoryAndName
} from './transformation.selectors';
import { TransformationType } from '../../enums/transformation-type';
import { EntityState } from '@ngrx/entity';
import { Transformation } from '../../model/transformation';
import { RevisionState } from '../../enums/revision-state';

describe('Transformation selectors', () => {
  function createMockEntityState(): EntityState<Transformation> {
    return {
      ids: ['mockId0', 'mockId1', 'mockId2', 'mockId3', 'mockId4', 'mockId5'],
      entities: {
        mockId0: {
          id: 'mockId0',
          revision_group_id: 'mockGroupId',
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
            inputs: [],
            outputs: []
          },
          test_wiring: {
            input_wirings: [],
            output_wirings: []
          }
        },
        mockId1: {
          id: 'mockId1',
          revision_group_id: 'mockGroupId',
          name: 'average',
          description: 'mock description',
          category: 'BASIC',
          version_tag: '0.0.1',
          released_timestamp: new Date().toISOString(),
          disabled_timestamp: new Date().toISOString(),
          state: RevisionState.RELEASED,
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
        },
        mockId2: {
          id: 'mockId2',
          revision_group_id: 'mockGroupId',
          name: 'divide',
          description: 'mock description',
          category: 'BASIC',
          version_tag: '0.0.1',
          released_timestamp: new Date().toISOString(),
          disabled_timestamp: new Date().toISOString(),
          state: RevisionState.RELEASED,
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
        },
        mockId3: {
          id: 'mockId3',
          revision_group_id: 'mockGroupId',
          name: 'LINEAR RUL',
          description: 'mock description',
          category: 'BASIC',
          version_tag: '0.0.1',
          released_timestamp: new Date().toISOString(),
          disabled_timestamp: new Date().toISOString(),
          state: RevisionState.RELEASED,
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
            inputs: [],
            outputs: []
          },
          test_wiring: {
            input_wirings: [],
            output_wirings: []
          }
        },
        mockId4: {
          id: 'mockId4',
          revision_group_id: 'mockGroupId',
          name: 'EXP RUL',
          description: 'mock description',
          category: 'BASIC',
          version_tag: '0.0.1',
          released_timestamp: new Date().toISOString(),
          disabled_timestamp: new Date().toISOString(),
          state: RevisionState.RELEASED,
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
            inputs: [],
            outputs: []
          },
          test_wiring: {
            input_wirings: [],
            output_wirings: []
          }
        },
        mockId5: {
          id: 'mockId5',
          revision_group_id: 'mockGroupId',
          name: 'OLD RUL',
          description: 'mock description',
          category: 'BASIC',
          version_tag: '0.0.1',
          released_timestamp: new Date().toISOString(),
          disabled_timestamp: new Date().toISOString(),
          state: RevisionState.DISABLED,
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
            inputs: [],
            outputs: []
          },
          test_wiring: {
            input_wirings: [],
            output_wirings: []
          }
        }
      }
    };
  }

  it('#selectTransformationsByCategoryAndName should filter for category "COMPONENT"', () => {
    // Arrange
    const mockEntityState = createMockEntityState();

    // Act
    const filteredTransformations = selectTransformationsByCategoryAndName(
      TransformationType.COMPONENT,
      null
    ).projector(mockEntityState);

    // Assert
    expect(filteredTransformations.EXAMPLES.length).toBe(1);
    expect(filteredTransformations.BASIC.length).toBe(2);
  });

  it('#selectTransformationsByCategoryAndName should filter for category "WORKFLOW"', () => {
    // Arrange
    const mockEntityState = createMockEntityState();

    // Act
    const filteredTransformations = selectTransformationsByCategoryAndName(
      TransformationType.WORKFLOW,
      null
    ).projector(mockEntityState);

    // Assert
    expect(filteredTransformations.BASIC.length).toBe(2);
  });

  it('#selectTransformationsByCategoryAndName should filter for category "COMPONENT" and name', () => {
    // Arrange
    const mockEntityState = createMockEntityState();
    const name = 'aver';

    // Act
    const filteredTransformations = selectTransformationsByCategoryAndName(
      TransformationType.COMPONENT,
      name
    ).projector(mockEntityState);

    // Assert
    expect(filteredTransformations.BASIC.length).toBe(1);
  });

  it('#selectTransformationsByCategoryAndName should filter for category "WORKFLOW" and name', () => {
    // Arrange
    const mockEntityState = createMockEntityState();
    const name = 'LIN';

    // Act
    const filteredTransformations = selectTransformationsByCategoryAndName(
      TransformationType.WORKFLOW,
      name
    ).projector(mockEntityState);

    // Assert
    expect(filteredTransformations.BASIC.length).toBe(1);
  });

  it('#selectTransformationsByCategoryAndName should filter out RevisionState "DISABLED"', () => {
    // Arrange
    const mockEntityState = createMockEntityState();
    const name = 'RUL';

    // Act
    const filteredTransformations = selectTransformationsByCategoryAndName(
      TransformationType.WORKFLOW,
      name
    ).projector(mockEntityState);

    // Assert
    expect(filteredTransformations.BASIC.length).toBe(2);
  });

  it('#selectHashedTransformationLookupById should return a transformation lookup tabelle by id', () => {
    // Arrange
    const mockEntityState = createMockEntityState();
    const ids = ['mockId3', 'mockId4'];

    // Act
    const transformations = selectAllTransformations.projector(mockEntityState);
    const hashedTransformationLookupById = selectHashedTransformationLookupById.projector(
      transformations
    );

    // Assert
    expect(hashedTransformationLookupById.mockId3.id).toBe(ids[0]);
    expect(hashedTransformationLookupById.mockId4.id).toBe(ids[1]);
  });

  it('#selectTransformationById should return a transformation selected by id', () => {
    // Arrange
    const mockEntityState = createMockEntityState();
    const id = 'mockId3';

    // Act
    const transformationById = selectTransformationById(id).projector(
      mockEntityState
    );

    // Assert
    expect(transformationById.id).toBe(id);
  });
});
