import { createReducer, on } from '@ngrx/store';
import {
  initialTransformationState,
  transformationEntityAdapter
} from './transformation.state';
import {
  addTransformation,
  removeTransformation,
  setAllTransformations,
  updateTransformation
} from './transformation.actions';

export const transformationReducers = createReducer(
  initialTransformationState,
  on(setAllTransformations, (state, action) => {
    return transformationEntityAdapter.setAll(action.payload, state);
  }),
  on(addTransformation, (state, action) => {
    return transformationEntityAdapter.setOne(action.payload, state);
  }),
  on(updateTransformation, (state, action) => {
    return transformationEntityAdapter.upsertOne(action.payload, state);
  }),
  on(removeTransformation, (state, action) => {
    return transformationEntityAdapter.removeOne(action.payload, state);
  })
);
