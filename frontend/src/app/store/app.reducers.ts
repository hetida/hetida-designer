import { ActionReducerMap } from '@ngrx/store';
import { tabItemReducers } from './tab-item/tab-item.reducers';
import { IAppState } from './app.state';
import { executionProtocolReducers } from './execution-protocol/execution-protocol.reducers';
import { transformationReducers } from './transformation/transformation.reducers';

export const appReducers: ActionReducerMap<IAppState, any> = {
  transformations: transformationReducers,
  tabItems: tabItemReducers,
  executionProtocol: executionProtocolReducers
};
