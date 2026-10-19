import { TabItem } from 'src/app/model/tab-item';
import { createEntityAdapter, EntityState } from '@ngrx/entity';

export const tabItemEntityAdapter = createEntityAdapter<TabItem>();

export interface ITabItemState extends EntityState<TabItem> {
  activeTabItemId: string | number | null;
}

export const initialTabItemState: ITabItemState =
  tabItemEntityAdapter.getInitialState({
    activeTabItemId: null
  });
