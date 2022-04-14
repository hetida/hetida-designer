import { createFeatureSelector, createSelector } from '@ngrx/store';
import { IAppState } from '../app.state';
import { ITabItemState, tabItemEntityAdapter } from './tab-item.state';
import { TabItem } from '../../model/tab-item';
import { selectHashedAbstractBaseItemLookupById } from '../base-item/base-item.selectors';
import { AbstractBaseItem, BaseItem } from '../../model/base-item';
import { isBaseItem } from '../base-item/base-item-guards';

export type TabItemWithBaseItem = Omit<TabItem, 'baseItemId'> & {
  baseItem: BaseItem;
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
  selectHashedAbstractBaseItemLookupById,
  (
    orderedTabItems: TabItem[],
    abstractBaseItems: Record<string, AbstractBaseItem>
  ) =>
    orderedTabItems.map((tabItem): TabItemWithBaseItem => {
      const abstractBaseItem = abstractBaseItems[tabItem.baseItemId];
      if (!isBaseItem(abstractBaseItem)) {
        throw Error(
          'Inconsistent state: Found a tab item whose base item was not yet expanded.'
        );
      }
      return {
        ...tabItem,
        baseItem: abstractBaseItem
      };
    })
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
