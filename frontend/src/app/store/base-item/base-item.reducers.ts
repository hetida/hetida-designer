import { createReducer, on } from '@ngrx/store';
import {
  addBaseItem,
  getBaseItems,
  patchComponentProperties,
  patchWorkflowProperties,
  putBaseItem,
  removeBaseItem
} from './base-item.actions';
import { baseItemEntityAdapter, initialBaseItemState } from './base-item.state';

export const baseItemReducers = createReducer(
  initialBaseItemState,
  on(getBaseItems, (state, action) => {
    return baseItemEntityAdapter.setAll(action.payload, state);
  }),
  on(addBaseItem, (state, action) => {
    return baseItemEntityAdapter.setOne(action.payload, state);
  }),
  on(putBaseItem, (state, action) => {
    const baseItem = action.payload;
    return baseItemEntityAdapter.updateOne(
      { id: baseItem.id, changes: baseItem },
      state
    );
  }),
  on(removeBaseItem, (state, action) => {
    return baseItemEntityAdapter.removeOne(action.payload, state);
  }),
  on(patchComponentProperties, patchWorkflowProperties, (state, action) => {
    return baseItemEntityAdapter.upsertOne(action.payload, state);
  })
);
