import { TreeControl } from '@angular/cdk/tree';
import { DataSourceSink } from 'src/app/service/http-service/adapter-http.service';
import { Utils } from 'src/app/utils/utils';

export interface FlatDataSourceSink extends DataSourceSink {
  parentId: string; // sameAsNodeId
}

export interface TreeNode {
  id: string;
  name: string;
  parentId: string;
  thingNodeId?: string;
}

export type TreeNodeWithLevelAndExpandableInfo<TN extends TreeNode> = TN & {
  expandable: boolean;
  level: number;
};

export class ThingConverter<T extends TreeNode> {
  private readonly sourceOrSinkNodes: FlatDataSourceSink[];
  private readonly sourcesOrSinksMap: Map<
    string,
    FlatDataSourceSink[]
  > = new Map();

  constructor(
    sourcesOrSinks: DataSourceSink[],
    private readonly textSearchParts: string[] = []
  ) {
    this.textSearchParts = textSearchParts.map(text => text.toLowerCase());
    this.sourceOrSinkNodes = sourcesOrSinks.map(s => {
      const tmp = {
        ...s,
        parentId: s.thingNodeId
      };

      if (!this.sourcesOrSinksMap.get(tmp.parentId)) {
        this.sourcesOrSinksMap.set(tmp.parentId, []);
      }

      this.sourcesOrSinksMap.get(tmp.parentId).push(tmp);
      return tmp;
    });
  }
  /**
   * Flatten a list of node type T to flattened version of node F.
   * Please note that type T may be nested, and the length of `structuredData` may be different
   * from that of returned list `F[]`.
   */
  flattenNodes(thingNodes: T[]): TreeNodeWithLevelAndExpandableInfo<T>[] {
    if (this.sourceOrSinkNodes.length === 0) {
      return [];
    }

    const allNodes: T[] = thingNodes.concat(this.sourceOrSinkNodes as any);

    const childNodeMap: Map<string, T[]> = allNodes.reduce((acc, node: T) => {
      const parentId = Utils.isDefined(node.parentId) ? node.parentId : null;

      if (!acc.has(parentId)) {
        acc.set(parentId, []);
      }
      acc.get(parentId).push(node);
      return acc;
    }, new Map());

    const childNodeMapWithoutDanglingNodes: Map<
      string,
      T[]
    > = this.danglingNodeElimination(childNodeMap);
    const nodesWithoutDanglingNodes = Array.from(
      childNodeMapWithoutDanglingNodes.values()
    ).reduce((acc, nodes) => [...acc, ...nodes], []);

    let filteredChildNodeMap: Map<string, T[]>;
    if (this.textSearchParts.length > 0) {
      const matchingNodeIds: Set<string> = nodesWithoutDanglingNodes.reduce(
        (acc, node: T) => {
          this.textSearchParts.forEach(textSearch => {
            if (node.name.toLowerCase().includes(textSearch)) {
              acc.add(node.id);
            }
          });
          return acc;
        },
        new Set<string>()
      );

      filteredChildNodeMap = this.createFilteredChildNodeMap(
        matchingNodeIds,
        childNodeMapWithoutDanglingNodes
      );
    } else {
      filteredChildNodeMap = childNodeMapWithoutDanglingNodes;
    }

    const sorted = this.sort(filteredChildNodeMap);
    const levelStructred = this.toLevelStructure(sorted);

    return levelStructred;
  }

  private danglingNodeElimination(
    initialChildNodeMap: Map<string, T[]>
  ): Map<string, T[]> {
    const filteredChildNodeMap: Map<string, T[]> = new Map();
    const rootNodes: T[] = initialChildNodeMap.has(null)
      ? initialChildNodeMap.get(null)
      : [];

    const isDanglingNode = (node: T): boolean => {
      const hasChildNodes = initialChildNodeMap.has(node.id);
      const childNodes = hasChildNodes ? initialChildNodeMap.get(node.id) : [];

      const isSinkOrSource = Utils.isDefined(node.thingNodeId) ? true : false;
      const selfIsDanglingNode = !hasChildNodes && !isSinkOrSource;
      const allChildrenAreDanglingNodes = hasChildNodes
        ? childNodes
            .map(isDanglingNode)
            .every(isDanglingNodeEvery => isDanglingNodeEvery)
        : false;
      const nodeIsDanglingNode =
        selfIsDanglingNode || allChildrenAreDanglingNodes;

      if (!nodeIsDanglingNode) {
        const parentId = node.parentId ?? null;
        if (!filteredChildNodeMap.has(parentId)) {
          filteredChildNodeMap.set(parentId, []);
        }

        filteredChildNodeMap.get(parentId).push(node);
      }

      return nodeIsDanglingNode;
    };

    rootNodes.forEach(isDanglingNode);

    return filteredChildNodeMap;
  }

  private createFilteredChildNodeMap(
    matchingNodes: Set<string>,
    childNodeMap: Map<string, T[]>
  ): Map<string, T[]> {
    const filteredChildNodeMap: Map<string, T[]> = new Map();

    const iterateChildren = (node: T, parentIsFiltered: boolean): boolean => {
      const parentId = node.parentId ?? null;

      if (!filteredChildNodeMap.has(parentId)) {
        filteredChildNodeMap.set(parentId, []);
      }

      let isFiltered = matchingNodes.has(node.id) || parentIsFiltered;

      const isAnyChildNodeFiltered = (childNodeMap.has(node.id)
        ? childNodeMap.get(node.id)
        : []
      )
        .map(childNode => iterateChildren(childNode, isFiltered))
        .some(childNodeIsFiltered => childNodeIsFiltered);

      if (isAnyChildNodeFiltered) {
        isFiltered = true;
      }

      if (isFiltered) {
        filteredChildNodeMap.get(parentId).push(node);
      }

      return isFiltered;
    };

    const rootNodes = childNodeMap.get(null);
    rootNodes.forEach(rootNode => {
      iterateChildren(rootNode, false);
    });

    return filteredChildNodeMap;
  }

  /**
   * Expand flattened node with current expansion status.
   * The returned list may have different length.
   */
  expandFlattenedNodes(
    nodes: TreeNodeWithLevelAndExpandableInfo<T>[],
    treeControl: TreeControl<TreeNodeWithLevelAndExpandableInfo<T>>
  ): TreeNodeWithLevelAndExpandableInfo<T>[] {
    const results: TreeNodeWithLevelAndExpandableInfo<T>[] = [];
    const currentExpand: boolean[] = [];
    currentExpand[0] = true;

    nodes.forEach(node => {
      let expand = true;
      for (let i = 0; i <= this.getLevel(node); i++) {
        expand = expand && currentExpand[i];
      }
      if (expand) {
        results.push(node);
      }
      if (this.isExpandable(node)) {
        currentExpand[this.getLevel(node) + 1] = treeControl.isExpanded(node);
      }
    });
    return results;
  }
  getLevel(node: TreeNodeWithLevelAndExpandableInfo<T>) {
    return node.level;
  }
  isExpandable(node: TreeNodeWithLevelAndExpandableInfo<T>) {
    return node.expandable;
  }

  /**
   *
   * The map "parentIdMap" should look like this
   *
   * "aParentId" => [{}, {}] (childs)
   *
   * @param filteredChildNodeMap a Map where all childs pro parentid are stored.
   */
  private sort(filteredChildNodeMap: Map<string, T[]>): T[] {
    const rootNodes = filteredChildNodeMap.get(null);
    const sortedArray = [...rootNodes];

    for (let i = 0; i < sortedArray.length; i++) {
      const value = sortedArray[i];
      const found = filteredChildNodeMap.get(value.id);
      if (found) {
        sortedArray.splice(i + 1, 0, ...found);
      }
    }
    return sortedArray;
  }

  /**
   *
   * adds level information to the sorted array:
   * expandable => has the current node any childs
   * level => how deep are the nodes.
   * @param sortedArray a sorted array where each parent are bevove there childs.
   */
  toLevelStructure(sortedArray: T[]): TreeNodeWithLevelAndExpandableInfo<T>[] {
    const sortedArrayWithLevelAndExpandableInfo: TreeNodeWithLevelAndExpandableInfo<
      T
    >[] = [];
    let anchestorIds: string[] = [];

    for (const currentNode of sortedArray) {
      const prevNodeParentId: string = anchestorIds[anchestorIds.length - 1];
      const expandable = Utils.isNullOrUndefined(currentNode.thingNodeId)
        ? true
        : false;

      // Check if current node is the root node.
      if (Utils.isNullOrUndefined(currentNode.parentId)) {
        // Root nodes have no anchestors.
        anchestorIds = [];
      }

      const levelOfParentNode = anchestorIds.findIndex(
        anchestorId => anchestorId === currentNode.parentId
      );

      if (levelOfParentNode === -1) {
        anchestorIds.push(currentNode.parentId);
      } else {
        if (prevNodeParentId !== currentNode.parentId) {
          anchestorIds.splice(levelOfParentNode);
          anchestorIds.push(currentNode.parentId);
        }
      }

      const level = anchestorIds.length - 1;
      sortedArrayWithLevelAndExpandableInfo.push({
        ...currentNode,
        level,
        expandable
      });
    }

    return sortedArrayWithLevelAndExpandableInfo;
  }
}
