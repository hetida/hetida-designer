import { createSelector } from '@ngrx/store';
import { IAppState } from '../app.state';

const executionProtocol = (state: IAppState) => state.executionProtocol;

export const selectExecutionProtocol = createSelector(
  executionProtocol,
  state => state.executionProtocol
);

export const selectExecutionProtocolLoading = createSelector(
  executionProtocol,
  state => state.loadingState
);
