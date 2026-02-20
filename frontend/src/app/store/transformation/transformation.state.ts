import { createEntityAdapter, EntityState } from '@ngrx/entity';
import { Transformation } from '../../model/transformation';

export const transformationEntityAdapter =
  createEntityAdapter<Transformation>();

export interface TransformationState extends EntityState<Transformation> {
  loaded: boolean;
}

export const initialTransformationState: TransformationState =
  transformationEntityAdapter.getInitialState({ loaded: false });
