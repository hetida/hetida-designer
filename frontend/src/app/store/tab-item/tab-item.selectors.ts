import { createFeatureSelector, createSelector } from '@ngrx/store';
import { IAppState } from '../app.state';
import { ITabItemState, tabItemEntityAdapter } from './tab-item.state';
import { TabItem } from '../../model/tab-item';
import { selectHashedTransformationLookupById } from '../transformation/transformation.selectors';
import { Transformation } from '../../model/new-api/transformation';

export type TabItemWithBaseItem = Omit<TabItem, 'transformationId'> & {
  baseItem: Transformation;
};

const { selectEntities, selectAll } = tabItemEntityAdapter.getSelectors();

const selectTabItemState = createFeatureSelector<IAppState, ITabItemState>(
  'tabItems'
);

export const selectOrderedTabItems = createSelector(
  selectTabItemState,
  (tabItemState): TabItem[] => selectAll(tabItemState)
);

export const selectOrderedTabItemsWithBaseItem = createSelector(
  selectOrderedTabItems,
  selectHashedTransformationLookupById,
  (
    orderedTabItems: TabItem[],
    transformations: Record<string, Transformation>
  ) =>
    orderedTabItems.map(
      (tabItem): TabItemWithBaseItem => {
        const transformation = transformations[tabItem.transformationId];
        if (!transformation) {
          throw Error(
            'Inconsistent state: Found a tab item whose transformation is not in store.'
          );
        }
        return {
          ...tabItem,
          baseItem: transformation
        };
      }
    )
);

const selectActiveTabItemId = createSelector(
  selectTabItemState,
  tabItemState => tabItemState.activeTabItemId
);

export const selectActiveTabItem = createSelector(
  selectActiveTabItemId,
  selectTabItemState,
  (activeTabItemId, tabItemState): TabItem | null => {
    return activeTabItemId === null
      ? null
      : selectEntities(tabItemState)[activeTabItemId];
  }
);
