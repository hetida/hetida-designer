import { ActionReducerMap } from '@ngrx/store';
import { tabItemReducers } from './tab-item/tab-item.reducers';
import { IAppState } from './app.state';
import { baseItemReducers } from './base-item/base-item.reducers';
import { executionProtocolReducers } from './execution-protocol/execution-protocol.reducers';
import { transformationRevisionReducers } from './transformation-revision/transformation-revision.reducers';

export const appReducers: ActionReducerMap<IAppState, any> = {
  baseItems: baseItemReducers,
  transformationRevisions: transformationRevisionReducers,
  tabItems: tabItemReducers,
  executionProtocol: executionProtocolReducers
};
