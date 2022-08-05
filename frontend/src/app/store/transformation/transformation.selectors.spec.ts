import { selectTransformationsByCategoryAndName } from './transformation.selectors';
import { BaseItemType } from '../../enums/base-item-type';
import { EntityState } from '@ngrx/entity';
import { Transformation } from '../../model/new-api/transformation';
import { RevisionState } from '../../enums/revision-state';

describe('Transformation selectors', () => {
  function createMockEntityState(): EntityState<Transformation> {
    return {
      ids: ['mockId0', 'mockId1', 'mockId2'],
      entities: {
        mockId0: {
          id: 'mockId0',
          revision_group_id: 'mockGroupId',
          name: 'mock transformation',
          description: 'mock description',
          category: 'DRAFT',
          version_tag: '0.0.1',
          released_timestamp: new Date().toISOString(),
          disabled_timestamp: new Date().toISOString(),
          state: RevisionState.DRAFT,
          type: BaseItemType.COMPONENT,
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
          name: 'mock transformation',
          description: 'mock description',
          category: 'DRAFT',
          version_tag: '0.0.1',
          released_timestamp: new Date().toISOString(),
          disabled_timestamp: new Date().toISOString(),
          state: RevisionState.RELEASED,
          type: BaseItemType.WORKFLOW,
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
          name: 'mock disabled transformation',
          description: 'mock description',
          category: 'DRAFT',
          version_tag: '0.0.1',
          released_timestamp: new Date().toISOString(),
          disabled_timestamp: new Date().toISOString(),
          state: RevisionState.DISABLED,
          type: BaseItemType.COMPONENT,
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
        }
      }
    };
  }

  it('#selectTransformationsByCategoryAndName should filter for category "COMPONENT"', () => {
    // Arrange
    const mockEntityState = createMockEntityState();

    // Act
    const filteredTransformations = selectTransformationsByCategoryAndName(
      BaseItemType.COMPONENT,
      null
    ).projector(mockEntityState);
    // Assert
    expect(filteredTransformations[0][1].length).toBe(1);
  });

  it('#selectTransformationsByCategoryAndName should filter for category "WORKFLOW"', () => {
    // Arrange
    const mockEntityState = createMockEntityState();

    // Act
    const filteredTransformations = selectTransformationsByCategoryAndName(
      BaseItemType.WORKFLOW,
      null
    ).projector(mockEntityState);

    // Assert
    expect(filteredTransformations[0][1].length).toBe(1);
  });

  it('#selectTransformationsByCategoryAndName should filter for category "COMPONENT" and name', () => {
    // Arrange
    const mockEntityState = createMockEntityState();
    const name = 'mock transformation';

    // Act
    const filteredTransformations = selectTransformationsByCategoryAndName(
      BaseItemType.COMPONENT,
      name
    ).projector(mockEntityState);

    // Assert
    expect(filteredTransformations[0][1].length).toBe(1);
  });

  it('#selectTransformationsByCategoryAndName should filter for category "WORKFLOW" and name', () => {
    // Arrange
    const mockEntityState = createMockEntityState();
    const name = 'mock transformation';

    // Act
    const filteredTransformations = selectTransformationsByCategoryAndName(
      BaseItemType.WORKFLOW,
      name
    ).projector(mockEntityState);

    // Assert
    expect(filteredTransformations[0][1].length).toBe(1);
  });

  it('#selectTransformationsByCategoryAndName should filter-out RevisionState "DISABLED"', () => {
    // Arrange
    const mockEntityState = createMockEntityState();
    const name = 'mock disabled transformation';

    // Act
    const filteredTransformations = selectTransformationsByCategoryAndName(
      BaseItemType.COMPONENT,
      name
    ).projector(mockEntityState);

    // Assert
    expect(filteredTransformations.length).toBe(0);
  });
});
