import { ITabItemState } from './tab-item/tab-item.state';
import { IBaseItemState } from './base-item/base-item.state';
import { IExecutionProtocolState } from './execution-protocol/execution-protocol.state';
import { TransformationRevisionState } from './transformation-revision/transformation-revision.state';

export interface IAppState {
  baseItems: IBaseItemState;
  transformationRevisions: TransformationRevisionState;
  tabItems: ITabItemState;
  executionProtocol: IExecutionProtocolState;
}
