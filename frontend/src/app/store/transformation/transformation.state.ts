import { createEntityAdapter, EntityState } from '@ngrx/entity';
import { Transformation } from '../../model/transformation';

export const transformationEntityAdapter =
  createEntityAdapter<Transformation>();

export type TransformationState = EntityState<Transformation>;

export const initialTransformationState: TransformationState =
  transformationEntityAdapter.getInitialState();
