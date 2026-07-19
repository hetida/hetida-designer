import { AdapterDataType, NodeSourceType } from '../adapter-http.service';

export interface NodeClickEvent {
  node: TreeNodeWithUiInfo;
  event: MouseEvent;
  nodeSourceType?: NodeSourceType;
  adapterUrl?: string;
}

export interface TreeNodeWithUiInfo {
  id: string;
  name: string;
  parentId: string | null;
  thingNodeId?: string;
  type?: AdapterDataType;
  filters?: any;
  metadataKey?: string;
  expandable: boolean;
  level: number;
  loading: boolean;
}
