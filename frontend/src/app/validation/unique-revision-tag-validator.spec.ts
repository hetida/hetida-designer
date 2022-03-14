import { FormControl } from '@angular/forms';
import { BaseItemType } from '../enums/base-item-type';
import { RevisionState } from '../enums/revision-state';
import { AbstractBaseItem } from '../model/base-item';
import { UniqueRevisionTagValidator } from './unique-revision-tag-validator';

describe('UniqueRevisionTagValidator', () => {
  const baseItems: Array<AbstractBaseItem> = [
    {
      id: 'abc',
      type: BaseItemType.COMPONENT,
      groupId: 'mygroup',
      name: 'Test Component',
      description: '',
      category: 'test',
      tag: '0.1.0',
      state: RevisionState.DRAFT,
      inputs: [],
      outputs: [],
      wirings: []
    },
    {
      id: 'abc',
      type: BaseItemType.WORKFLOW,
      groupId: 'mygroup',
      name: 'Test Workflow',
      description: '',
      category: 'test',
      tag: '1.0.0',
      state: RevisionState.DRAFT,
      inputs: [],
      outputs: [],
      wirings: []
    }
  ];

  it('UniqueRevisionTagValidator should return valid for unnused revision tags', () => {
    const formControl = new FormControl(
      '1.0.1',
      UniqueRevisionTagValidator(baseItems)
    );
    expect(formControl.valid).toBe(true);
  });

  xit('UniqueRevisionTagValidator should return invalid for duplicate revision tags', () => {
    const formControl = new FormControl(
      '1.0.0',
      UniqueRevisionTagValidator(baseItems)
    );
    expect(formControl.valid).toBe(false);
  });
});
