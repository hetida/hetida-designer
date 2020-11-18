import { createAction } from '@ngrx/store';
import { TabItem } from 'src/app/model/tab-item';

export const addTabItem = createAction(
  '[TabItem] Add TabItem',
  (payload: Omit<TabItem, 'id'>) => ({ payload })
);

export const removeTabItem = createAction(
  '[TabItem] Remove TabItem',
  (payload: string) => ({ payload })
);

export const setActiveTabItem = createAction(
  '[TabItem] Set ActiveTabItem',
  (payload: string) => ({ payload })
);

export const unsetActiveTabItem = createAction('[TabItem] Unset ActiveTabItem');
