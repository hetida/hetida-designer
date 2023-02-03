import { createAction } from '@ngrx/store';
import { ExecutionResponse } from '../../components/protocol-viewer/protocol-viewer.component';
import { Transformation } from '../../model/transformation';

export const setExecutionProtocol = createAction(
  '[ExecutionProtocol] Set ExecutionProtocol',
  (payload?: ExecutionResponse | Transformation | string) => {
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
