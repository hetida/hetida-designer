import { createAction } from '@ngrx/store';
import { ComponentBaseItem } from 'src/app/model/component-base-item';
import { Transformation } from 'src/app/model/new-api/transformation';
import { WorkflowBaseItem } from 'src/app/model/workflow-base-item';

export const setExecutionProtocol = createAction(
  '[ExecutionProtocol] Set ExecutionProtocol',
  (
    payload?: Transformation | WorkflowBaseItem | ComponentBaseItem | string
  ) => {
    if (payload !== undefined) {
      payload = JSON.stringify(payload, null, '\t').replace('\\n', '\n');
    } else {
      payload = undefined;
    }
    return { payload };
  }
);

export const setExecutionRunning = createAction('[ExecutionProtocol] Running');

export const setExecutionFinished = createAction(
  '[ExecutionProtocol] Finished'
);
