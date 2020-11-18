import { ITabItemState } from './tab-item/tab-item.state';
import { IBaseItemState } from './base-item/base-item.state';
import { IExecutionProtocolState } from './execution-protocol/execution-protocol.state';

export interface IAppState {
  baseItems: IBaseItemState;
  tabItems: ITabItemState;
  executionProtocol: IExecutionProtocolState;
}
