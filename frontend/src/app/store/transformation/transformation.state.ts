import { createEntityAdapter, EntityState } from '@ngrx/entity';
import { Transformation } from '../../model/new-api/transformation';

export const transformationEntityAdapter = createEntityAdapter<Transformation>();

export interface TransformationState extends EntityState<Transformation> {}

export const initialTransformationState: TransformationState = transformationEntityAdapter.getInitialState();
