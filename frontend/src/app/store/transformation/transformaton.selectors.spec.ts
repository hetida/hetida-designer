import { selectTransformationsByCategoryAndName } from './transformaton.selectors';
import { BaseItemType } from '../../enums/base-item-type';
import { EntityState } from '@ngrx/entity';
import { Transformation } from '../../model/new-api/transformation';
import { RevisionState } from '../../enums/revision-state';

describe('Transformation selectors', () => {
  it('#selectTransformationsByCategory should filter for category "COMPONENT"', () => {
    // arrange
    const mockEntityState: EntityState<Transformation> = {
      ids: ['abc'],
      entities: {
        abc: {
          id: 'abc',
          revision_group_id: 'groupId',
          name: 'Test Transformation',
          description: 'test description',
          category: 'DRAFT',
          version_tag: '0.1.0',
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
        }
      }
    };

    // act
    const filteredTransformations = selectTransformationsByCategoryAndName(
      BaseItemType.COMPONENT,
      null
    ).projector(mockEntityState);

    // assert
    expect(filteredTransformations.DRAFT.length).toBe(1);
  });
});
