import {
  selectAllTransformationRevisions,
  selectTransformationRevisionsByCategory
} from './transformaton-revision.selectors';

describe('Transformaton revision selectors', () => {
  enum BaseItemType {
    COMPONENT = 'COMPONENT',
    WORKFLOW = 'WORKFLOW'
  }

  it('should select transformation revisions by category', () => {
    const transformationRevisions = selectAllTransformationRevisions.projector();

    const components = selectTransformationRevisionsByCategory(
      BaseItemType.COMPONENT
    );

    const workflows = selectTransformationRevisionsByCategory(
      BaseItemType.WORKFLOW
    );

    expect(components);
    expect(workflows);
  });
});
