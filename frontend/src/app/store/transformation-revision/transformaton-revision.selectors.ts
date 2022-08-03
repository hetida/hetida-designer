import { createFeatureSelector, createSelector } from '@ngrx/store';
import { BaseItemType } from 'src/app/enums/base-item-type';
import { TransformationRevision } from 'src/app/model/new-api/transformation-revision';
import { Utils } from 'src/app/utils/utils';
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

export const selectTransformationRevisionsByCategoryAndName = (
  transformationRevisionType?: BaseItemType,
  transformationRevisionNameFilter?: string
) => {
  return createSelector(
    selectTransformationRevisionState,
    (state: TransformationRevisionState) => {
      return Object.values(state.entities)
        .filter(
          transformationRevision =>
            transformationRevision.type === transformationRevisionType
        )
        .filter(
          transformationRevision =>
            transformationRevision.state !== RevisionState.DISABLED
        )
        .filter(transformationRevision =>
          Utils.string.isEmptyOrUndefined(transformationRevisionNameFilter)
            ? true
            : transformationRevision.name
                .toLowerCase()
                .includes(transformationRevisionNameFilter.toLowerCase())
        )
        .reduce((acc, transformationRevision) => {
          if (Utils.isNullOrUndefined(acc[transformationRevision.category])) {
            acc[transformationRevision.category] = [];
          }
          acc[transformationRevision.category].push(transformationRevision);
          return acc;
        }, {} as { [category: string]: TransformationRevision[] });
    }
  );
};
