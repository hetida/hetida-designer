import { fakeAsync, tick } from '@angular/core/testing';
import {
  selectAllTransformationRevisions,
  selectTransformationRevisionsByCategory
} from './transformaton-revision.selectors';

describe('Transformaton revision selectors', () => {
  enum BaseItemType {
    COMPONENT = 'COMPONENT',
    WORKFLOW = 'WORKFLOW'
  }

  it('should select transformation revisions by category', fakeAsync(() => {
    const transformationRevisions = selectAllTransformationRevisions.projector();
    tick();
    const components = selectTransformationRevisionsByCategory(
      BaseItemType.COMPONENT
    );

    const workflows = selectTransformationRevisionsByCategory(
      BaseItemType.WORKFLOW
    );

    expect(transformationRevisions);
    expect(components);
    expect(workflows);
  }));
});
