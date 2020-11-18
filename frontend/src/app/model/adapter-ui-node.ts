import { TreeNodeSourceType } from '../components/tree-node/tree-node.component';

export interface AdapterUiFlatNode {
  id: any;
  parentId: string;
  thingNodeId: string;
  name: string;
  dataType?: string;
  dataSourceType?: TreeNodeSourceType;
  filters?: any;
  level: number;
  expandable: boolean;
}
