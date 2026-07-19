import { SourceSinkNode, ThingNode } from '../adapter-http.service';
import { TreeNodeWithUiInfo } from '../node-click/node-click';

export class ThingConverter {
  static addExtendedNodeInformation(
    parentLevel: number,
    thingNodes: ThingNode[],
    sourcesOrSinks: SourceSinkNode[]
  ): TreeNodeWithUiInfo[] {
    const sourcesOrSinksExpanded: TreeNodeWithUiInfo[] = sourcesOrSinks.map(
      sourceOrSink => ({
        ...sourceOrSink,
        expandable: false,
        level: parentLevel + 1,
        loading: false,
        parentId: sourceOrSink.thingNodeId,
        metadataKey: sourceOrSink.metadataKey
      })
    );

    const thingNodesExpanded: TreeNodeWithUiInfo[] = thingNodes.map(
      (thingNode): TreeNodeWithUiInfo => {
        return {
          ...thingNode,
          level: parentLevel + 1,
          expandable: true,
          loading: false
        };
      }
    );

    return sourcesOrSinksExpanded.concat(thingNodesExpanded);
  }
}
