import { createAction } from '@ngrx/store';
import { Transformation } from '../../model/new-api/transformation';

export const setAllTransformations = createAction(
  '[Transformation] Set All',
  (payload: Transformation[]) => ({ payload })
);

export const addTransformation = createAction(
  '[Transformation] Add Transformation Success',
  (payload: Transformation) => ({ payload })
);

export const updateTransformation = createAction(
  '[Transformation] Update Transformation',
  (payload: Transformation) => ({ payload })
);

export const removeTransformation = createAction(
  '[Transformation] Remove Transformation',
  (payload: string) => ({ payload })
);
