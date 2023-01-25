import { FormControl } from '@angular/forms';
import { BaseItemType } from '../enums/base-item-type';
import { RevisionState } from '../enums/revision-state';
import { Transformation } from '../model/new-api/transformation';

import { UniqueRevisionTagValidator } from './unique-revision-tag-validator';

describe('UniqueRevisionTagValidator', () => {
  const transformations: Array<Transformation> = [
    {
      id: 'mockId',
      revision_group_id: 'mockGroupId',
      name: 'mock transformation',
      description: 'mock description',
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
    },
    {
      id: 'mockId',
      revision_group_id: 'mockGroupId',
      name: 'mock transformation',
      description: 'mock description',
      category: 'DRAFT',
      version_tag: '1.0.0',
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
  ];

  it('UniqueRevisionTagValidator should return valid for unnused revision tags', () => {
    const formControl = new FormControl(
      '1.0.1',
      UniqueRevisionTagValidator(transformations)
    );
    expect(formControl.valid).toBe(true);
  });

  xit('UniqueRevisionTagValidator should return invalid for duplicate revision tags', () => {
    const formControl = new FormControl(
      '1.0.0',
      UniqueRevisionTagValidator(transformations)
    );
    expect(formControl.valid).toBe(false);
  });
});
