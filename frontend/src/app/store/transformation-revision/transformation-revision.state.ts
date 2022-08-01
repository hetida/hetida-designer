import { createEntityAdapter, EntityState } from '@ngrx/entity';
import { TransformationRevision } from '../../model/new-api/transformation-revision';

export const transformationRevisionEntityAdapter = createEntityAdapter<TransformationRevision>();

export interface TransformationRevisionState
  extends EntityState<TransformationRevision> {}

export const initialTransformationRevisionState: TransformationRevisionState = transformationRevisionEntityAdapter.getInitialState();
