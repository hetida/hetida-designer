export interface IExecutionProtocolState {
  loadingState: boolean;
  executionProtocol?: string;
}

export const initialExecutionProtocolState: IExecutionProtocolState = {
  executionProtocol: undefined,
  loadingState: false
};
