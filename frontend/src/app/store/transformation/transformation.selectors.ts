import { createFeatureSelector, createSelector } from '@ngrx/store';
import { TransformationType } from 'src/app/enums/transformation-type';
import { Transformation } from 'src/app/model/transformation';
import { Utils } from 'src/app/utils/utils';
import { RevisionState } from '../../enums/revision-state';
import {
  transformationEntityAdapter,
  TransformationState
} from './transformation.state';

const { selectAll, selectEntities } =
  transformationEntityAdapter.getSelectors();

export const selectTransformationState =
  createFeatureSelector<TransformationState>('transformations');

export const selectAllTransformations = createSelector(
  selectTransformationState,
  (state: TransformationState) =>
    selectAll(state).filter(
      transformationRevision =>
        transformationRevision.state !== RevisionState.DISABLED || true
    )
);

export const selectHashedTransformationLookupById = createSelector(
  selectAllTransformations,
  (transformations): Record<string, Transformation> => {
    // Fill one object instead of spreading the accumulator in each step, which
    // is quadratic in the number of transformations (~1 s for 3000 revisions).
    const lookup: Record<string, Transformation> = {};
    for (const transformation of transformations) {
      lookup[transformation.id] = transformation;
    }
    return lookup;
  }
);

export const selectTransformationById = (transformationId: string) =>
  createSelector(
    selectTransformationState,
    (state: TransformationState) => selectEntities(state)[transformationId]
  );

function filterByName(transformation: Transformation, name: string) {
  return Utils.string.isEmptyOrUndefined(name)
    ? true
    : transformation.name.toLowerCase().includes(name.toLowerCase());
}

/**
 * Selects transformations from the store, filtering them by transformationType and name.
 * Returns a key value object with the categories as keys and the corresponding transformations as values.
 */
export const selectTransformationsByCategoryAndName = (
  transformationType: TransformationType,
  name?: string,
  includeDeprecated: boolean = false
) => {
  return createSelector(
    selectTransformationState,
    (state: TransformationState) => {
      return Object.values(state.entities)
        .filter(transformation => transformation.type === transformationType)
        .filter(
          transformation =>
            transformation.state !== RevisionState.DISABLED || includeDeprecated
        )
        .filter(transformation => filterByName(transformation, name))
        .reduce(
          (acc, transformation) => {
            if (Utils.isNullOrUndefined(acc[transformation.category])) {
              acc[transformation.category] = [];
            }
            acc[transformation.category].push(transformation);
            return acc;
          },
          {} as { [category: string]: Transformation[] }
        );
    }
  );
};

export const selectTransformationsByRevisionGroupId = (
  transformationType: TransformationType,
  revGroupId: string,
  includeDeprecated: boolean = false
) => {
  return createSelector(
    selectTransformationState,
    (state: TransformationState) => {
      return Object.values(state.entities)
        .filter(
          transformation => transformation.revision_group_id === revGroupId
        )
        .filter(transformation => transformation.type === transformationType)
        .filter(
          transformation =>
            transformation.state !== RevisionState.DISABLED || includeDeprecated
        );
    }
  );
};

export const selectTransformationsLoaded = createSelector(
  selectTransformationState,
  (state: TransformationState) => state.loaded
);
