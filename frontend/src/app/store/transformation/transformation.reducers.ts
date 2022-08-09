import { createReducer, on } from '@ngrx/store';
import {
  initialTransformationState,
  transformationEntityAdapter
} from './transformation.state';
import {
  addTransformation,
  setAllTransformations
} from './transformation.actions';

export const transformationReducers = createReducer(
  initialTransformationState,
  on(setAllTransformations, (state, action) => {
    return transformationEntityAdapter.setAll(action.payload, state);
  }),
  on(addTransformation, (state, action) => {
    return transformationEntityAdapter.setOne(action.payload, state);
  })
);
