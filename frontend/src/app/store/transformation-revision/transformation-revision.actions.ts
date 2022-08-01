import { createAction } from '@ngrx/store';
import { TransformationRevision } from '../../model/new-api/transformation-revision';

export const setAllTransformationRevisions = createAction(
  '[TransformationRevision] Set All',
  (payload: TransformationRevision[]) => ({ payload })
);
