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
        transformationRevision.state !== RevisionState.DISABLED
    )
);

export const selectHashedTransformationLookupById = createSelector(
  selectAllTransformations,
  (transformations): Record<string, Transformation> =>
    transformations.reduce(
      (acc, transformation): Record<string, Transformation> => ({
        ...acc,
        [transformation.id]: transformation
      }),
      {}
    )
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
  name?: string
) => {
  return createSelector(
    selectTransformationState,
    (state: TransformationState) => {
      return Object.values(state.entities)
        .filter(transformation => transformation.type === transformationType)
        .filter(
          transformation => transformation.state !== RevisionState.DISABLED
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
