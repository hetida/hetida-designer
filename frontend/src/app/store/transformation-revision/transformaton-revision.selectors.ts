import { createFeatureSelector, createSelector } from '@ngrx/store';
import { RevisionState } from '../../enums/revision-state';
import {
  transformationRevisionEntityAdapter,
  TransformationRevisionState
} from './transformation-revision.state';

const { selectAll } = transformationRevisionEntityAdapter.getSelectors();

const selectTransformationRevisionState = createFeatureSelector<TransformationRevisionState>(
  'transformationRevisions'
);

// TODO do we need this?
export const selectAllTransformationRevisions = createSelector(
  selectTransformationRevisionState,
  (state: TransformationRevisionState) =>
    selectAll(state).filter(
      transformationRevision =>
        transformationRevision.state !== RevisionState.DISABLED
    )
);
