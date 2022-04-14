import { createFeatureSelector, createSelector } from '@ngrx/store';
import { AbstractBaseItem, BaseItem } from 'src/app/model/base-item';
import { ComponentBaseItem } from 'src/app/model/component-base-item';
import { WorkflowBaseItem } from 'src/app/model/workflow-base-item';
import { Utils } from 'src/app/utils/utils';
import { BaseItemType } from '../../enums/base-item-type';
import { RevisionState } from '../../enums/revision-state';
import { IAppState } from '../app.state';
import {
  isBaseItem,
  isComponentBaseItem,
  isWorkflowBaseItem
} from './base-item-guards';
import { baseItemEntityAdapter, IBaseItemState } from './base-item.state';

const { selectAll, selectEntities } = baseItemEntityAdapter.getSelectors();

const selectBaseItemState = createFeatureSelector<IAppState, IBaseItemState>(
  'baseItems'
);

export const selectAbstractBaseItems = createSelector(
  selectBaseItemState,
  (state: IBaseItemState) =>
    selectAll(state).filter(
      baseItem => baseItem.state !== RevisionState.DISABLED
    )
);

export const selectHashedAbstractBaseItemLookupById = createSelector(
  selectAbstractBaseItems,
  (abstractBaseItems): Record<string, AbstractBaseItem> =>
    abstractBaseItems.reduce(
      (acc, abstractBaseItem): Record<string, AbstractBaseItem> => ({
        ...acc,
        [abstractBaseItem.id]: abstractBaseItem
      }),
      {}
    )
);

export const selectAbstractComponentBaseItems = createSelector(
  selectBaseItemState,
  (state: IBaseItemState): AbstractBaseItem[] =>
    selectAll(state).filter(
      baseItem =>
        baseItem.type === BaseItemType.COMPONENT &&
        baseItem.state !== RevisionState.DISABLED
    )
);

export const selectAbstractWorkflowBaseItems = createSelector(
  selectBaseItemState,
  (state: IBaseItemState) =>
    selectAll(state).filter(
      baseItem =>
        baseItem.type === BaseItemType.WORKFLOW &&
        baseItem.state !== RevisionState.DISABLED
    )
);

export const selectComponentBaseItemById = (workflowBaseItemId: string) =>
  createSelector(
    selectBaseItemState,
    (state: IBaseItemState): ComponentBaseItem => {
      const componentBaseItem = selectEntities(state)[workflowBaseItemId];
      Utils.assert(isComponentBaseItem(componentBaseItem));
      return componentBaseItem;
    }
  );

export const selectWorkflowBaseItemById = (workflowBaseItemId: string) =>
  createSelector(
    selectBaseItemState,
    (state: IBaseItemState): WorkflowBaseItem => {
      const workflowBaseItem = selectEntities(state)[workflowBaseItemId];
      Utils.assert(isWorkflowBaseItem(workflowBaseItem));
      return workflowBaseItem;
    }
  );

export const selectBaseItemById = (baseItemId: string) =>
  createSelector(
    selectAbstractBaseItemById(baseItemId),
    (abstractBaseItem): BaseItem | undefined => {
      if (Utils.isNullOrUndefined(abstractBaseItem)) {
        return undefined;
      }
      Utils.assert(isBaseItem(abstractBaseItem));
      return abstractBaseItem;
    }
  );

export const selectAbstractBaseItemById = (abstractBaseItemId: string) =>
  createSelector(
    selectBaseItemState,
    (state: IBaseItemState) => selectEntities(state)[abstractBaseItemId]
  );

export const selectBaseItemsByCategory = (
  baseItemType: BaseItemType,
  baseItemNameFilter?: string
) => {
  return createSelector(selectBaseItemState, (state: IBaseItemState) => {
    return Object.values(state.entities)
      .filter(abstractBaseItem => abstractBaseItem.type === baseItemType)
      .filter(
        abstractBaseItem => abstractBaseItem.state !== RevisionState.DISABLED
      )
      .filter(abstractBaseItem =>
        Utils.string.isEmptyOrUndefined(baseItemNameFilter)
          ? true
          : abstractBaseItem.name
              .toLowerCase()
              .includes(baseItemNameFilter.toLowerCase())
      )
      .reduce((acc, abstractBaseItem) => {
        if (Utils.isNullOrUndefined(acc[abstractBaseItem.category])) {
          acc[abstractBaseItem.category] = [];
        }
        acc[abstractBaseItem.category].push(abstractBaseItem);
        return acc;
      }, {} as { [category: string]: AbstractBaseItem[] });
  });
};
