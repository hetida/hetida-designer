import { TabItem } from 'src/app/model/tab-item';
import { createEntityAdapter, EntityState } from '@ngrx/entity';

export const tabItemEntityAdapter = createEntityAdapter<TabItem>();

export interface ITabItemState extends EntityState<TabItem> {
  ids: string[];
  activeTabItemId: string | null;
}

export const initialTabItemState: ITabItemState = tabItemEntityAdapter.getInitialState(
  {
    ids: [],
    activeTabItemId: null
  }
);
