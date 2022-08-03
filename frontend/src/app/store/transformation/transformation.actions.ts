import { createAction } from '@ngrx/store';
import { Transformation } from '../../model/new-api/transformation';

export const setAllTransformations = createAction(
  '[Transformation] Set All',
  (payload: Transformation[]) => ({ payload })
);
