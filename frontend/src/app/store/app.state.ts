import { ITabItemState } from './tab-item/tab-item.state';
import { IExecutionProtocolState } from './execution-protocol/execution-protocol.state';
import { TransformationState } from './transformation/transformation.state';

export interface IAppState {
  transformations: TransformationState;
  tabItems: ITabItemState;
  executionProtocol: IExecutionProtocolState;
}
