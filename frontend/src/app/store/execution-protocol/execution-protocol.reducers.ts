import { createReducer, on } from '@ngrx/store';
import {
  setExecutionFinished,
  setExecutionProtocol,
  setExecutionRunning
} from './execution-protocol.actions';
import { initialExecutionProtocolState } from './execution-protocol.state';

export const executionProtocolReducers = createReducer(
  initialExecutionProtocolState,
  on(setExecutionProtocol, (state, action) => ({
    ...state,
    executionProtocol: action.payload as string
  })),
  on(setExecutionRunning, state => ({
    ...state,
    loadingState: true
  })),
  on(setExecutionFinished, state => ({
    ...state,
    loadingState: false
  }))
);
