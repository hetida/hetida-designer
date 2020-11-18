import { createAction } from '@ngrx/store';
import { ComponentBaseItem } from 'src/app/model/component-base-item';
import { WorkflowBaseItem } from 'src/app/model/workflow-base-item';
import { AbstractBaseItem } from '../../model/base-item';

export const getBaseItems = createAction(
  '[BaseItem] Get BaseItems Success',
  (payload: AbstractBaseItem[]) => ({ payload })
);

export const addBaseItem = createAction(
  '[BaseItem] Add BaseItem Success',
  (payload: AbstractBaseItem) => ({ payload })
);

export const patchComponentProperties = createAction(
  '[BaseItem] Patch Component Properties',
  (payload: ComponentBaseItem) => ({ payload })
);

export const patchWorkflowProperties = createAction(
  '[BaseItem] Patch Component Properties',
  (payload: WorkflowBaseItem) => ({ payload })
);

export const putBaseItem = createAction(
  '[BaseItem] Put BaseItem Success',
  (payload: AbstractBaseItem) => ({ payload })
);

export const removeBaseItem = createAction(
  '[BaseItem] Remove BaseItem',
  (payload: string) => ({ payload })
);
