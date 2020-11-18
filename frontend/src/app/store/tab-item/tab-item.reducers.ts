import { createReducer, on } from '@ngrx/store';
import { RevisionState } from 'src/app/enums/revision-state';
import { TabItem } from '../../model/tab-item';
import { putBaseItem, removeBaseItem } from '../base-item/base-item.actions';
import {
  addTabItem,
  removeTabItem,
  setActiveTabItem,
  unsetActiveTabItem
} from './tab-item.actions';
import {
  initialTabItemState,
  ITabItemState,
  tabItemEntityAdapter
} from './tab-item.state';

const { selectAll } = tabItemEntityAdapter.getSelectors();

const closeAllBaseItemRelatedTabs = (
  baseItemIdToRemove: string,
  state: ITabItemState
): ITabItemState => {
  // Find all tabs that correspond to the deleted base item.
  const tabItemIdsToClose = selectAll(state)
    .filter(tabItem => tabItem.baseItemId === baseItemIdToRemove)
    .map(tabItem => tabItem.id);

  // Immediately close all tabs whose corresponding base item has being
  // deleted.
  const updatedState = tabItemEntityAdapter.removeMany(
    tabItemIdsToClose.map(tabItemIdToClose => tabItemIdToClose),
    state
  );

  // Check whether one of the deleted tabs was the active tab.
  return tabItemIdsToClose.reduce(
    (acc, tabItemIdToClose): ITabItemState =>
      unsetActiveTabItemIfPointingToDeletedTabItem(acc, tabItemIdToClose),
    updatedState
  );
};

const unsetActiveTabItemIfPointingToDeletedTabItem = (
  tabItemState: ITabItemState,
  tabItemIdToRemove: string
) => {
  // Whenever we remove a tab item we might have to update the active tab item id to keep
  // the state consistent if the removed tab item was the active one.
  let activeTabItemId = tabItemState.activeTabItemId;
  if (tabItemState.activeTabItemId === tabItemIdToRemove) {
    const numUpdatedTabItemIds = tabItemState.ids.length;
    activeTabItemId =
      numUpdatedTabItemIds > 0
        ? tabItemState.ids[numUpdatedTabItemIds - 1]
        : null;
  }

  return {
    ...tabItemState,
    activeTabItemId
  };
};

export const tabItemReducers = createReducer(
  initialTabItemState,
  on(
    addTabItem,
    (state, action): ITabItemState => {
      const tabItemToAdd: TabItem = {
        id: `${action.payload.baseItemId}-${action.payload.tabItemType}`,
        ...action.payload
      };
      const updatedState = tabItemEntityAdapter.addOne(tabItemToAdd, state);
      return {
        ...updatedState,
        // Whenever we add a new tab item it will be immediately activated.
        activeTabItemId: tabItemToAdd.id
      };
    }
  ),
  on(
    removeTabItem,
    (state, action): ITabItemState => {
      const tabItemIdToRemove = action.payload;
      const updatedState = tabItemEntityAdapter.removeOne(
        tabItemIdToRemove,
        state
      );

      // Check whether the deleted tab was the active tab.
      return unsetActiveTabItemIfPointingToDeletedTabItem(
        updatedState,
        tabItemIdToRemove
      );
    }
  ),
  on(putBaseItem, (state, action) => {
    if (action.payload.state === RevisionState.DISABLED) {
      const baseItemIdToRemove = action.payload.id;
      return closeAllBaseItemRelatedTabs(baseItemIdToRemove, state);
    }
    return state;
  }),
  on(
    removeBaseItem,
    (state, action): ITabItemState => {
      const baseItemIdToRemove = action.payload;
      return closeAllBaseItemRelatedTabs(baseItemIdToRemove, state);
    }
  ),
  on(
    setActiveTabItem,
    (state, action): ITabItemState => ({
      ...state,
      activeTabItemId: action.payload
    })
  ),
  on(
    unsetActiveTabItem,
    (state): ITabItemState => ({
      ...state,
      activeTabItemId: null
    })
  )
);
