import { FormControl } from '@angular/forms';
import { TransformationType } from '../enums/transformation-type';
import { RevisionState } from '../enums/revision-state';
import { Transformation } from '../model/transformation';
import { UniqueVersionTagValidator } from './unique-version-tag-validator';

describe('UniqueVersionTagValidator', () => {
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
    }
  ];

  it('UniqueVersionTagValidator should return valid for unnused version tags', () => {
    const formControl = new FormControl(
      '1.0.1',
      UniqueVersionTagValidator(transformations)
    );
    expect(formControl.valid).toBe(true);
  });

  xit('UniqueVersionTagValidator should return invalid for duplicate version tags', () => {
    const formControl = new FormControl(
      '1.0.0',
      UniqueVersionTagValidator(transformations)
    );
    expect(formControl.valid).toBe(false);
  });
});
