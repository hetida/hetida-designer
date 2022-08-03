import { createReducer, on } from '@ngrx/store';
import {
  initialTransformationState,
  transformationEntityAdapter
} from './transformation.state';
import { setAllTransformations } from './transformation.actions';

export const transformationReducers = createReducer(
  initialTransformationState,
  on(setAllTransformations, (state, action) => {
    return transformationEntityAdapter.setAll(action.payload, state);
  })
);
