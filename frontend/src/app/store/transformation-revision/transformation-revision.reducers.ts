import { createReducer, on } from '@ngrx/store';
import {
  initialTransformationRevisionState,
  transformationRevisionEntityAdapter
} from './transformation-revision.state';
import { setAllTransformationRevisions } from './transformation-revision.actions';

export const transformationRevisionReducers = createReducer(
  initialTransformationRevisionState,
  on(setAllTransformationRevisions, (state, action) => {
    return transformationRevisionEntityAdapter.setAll(action.payload, state);
  })
);
