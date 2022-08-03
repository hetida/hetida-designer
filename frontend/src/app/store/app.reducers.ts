import { ActionReducerMap } from '@ngrx/store';
import { tabItemReducers } from './tab-item/tab-item.reducers';
import { IAppState } from './app.state';
import { baseItemReducers } from './base-item/base-item.reducers';
import { executionProtocolReducers } from './execution-protocol/execution-protocol.reducers';
import { transformationReducers } from './transformation/transformation.reducers';

export const appReducers: ActionReducerMap<IAppState, any> = {
  baseItems: baseItemReducers,
  transformations: transformationReducers,
  tabItems: tabItemReducers,
  executionProtocol: executionProtocolReducers
};
