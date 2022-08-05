import { createFeatureSelector, createSelector } from '@ngrx/store';
import { BaseItemType } from 'src/app/enums/base-item-type';
import { Transformation } from 'src/app/model/new-api/transformation';
import { Utils } from 'src/app/utils/utils';
import { RevisionState } from '../../enums/revision-state';
import {
  transformationEntityAdapter,
  TransformationState
} from './transformation.state';

const { selectAll } = transformationEntityAdapter.getSelectors();

const selectTransformationState = createFeatureSelector<TransformationState>(
  'transformations'
);

// TODO do we need this, change name selectAllTransformations?
export const selectAllTransformationRevisions = createSelector(
  selectTransformationState,
  (state: TransformationState) =>
    selectAll(state).filter(
      transformationRevision =>
        transformationRevision.state !== RevisionState.DISABLED
    )
);

function filterByName(transformation: Transformation, name: string) {
  return Utils.string.isEmptyOrUndefined(name)
    ? true
    : transformation.name.toLowerCase().includes(name.toLowerCase());
}

export const selectTransformationsByCategoryAndName = (
  transformationType: BaseItemType,
  name?: string
) => {
  return createSelector(
    selectTransformationState,
    (state: TransformationState) => {
      const filteredTransformations = Object.values(state.entities)
        .filter(transformation => transformation.type === transformationType)
        .filter(
          transformation => transformation.state !== RevisionState.DISABLED
        )
        .filter(transformation => filterByName(transformation, name))
        .reduce((acc, transformation) => {
          if (Utils.isNullOrUndefined(acc[transformation.category])) {
            acc[transformation.category] = [];
          }
          acc[transformation.category].push(transformation);
          return acc;
        }, {} as { [category: string]: Transformation[] });

      // TODO sort categories alphabetically
      const sortAlphabeticallyTransformations = Object.entries(
        filteredTransformations
      ).sort(([categoryNameA], [categoryNameB]) =>
        Utils.string.compare(categoryNameA, categoryNameB)
      );
      return sortAlphabeticallyTransformations;
    }
  );
};
