import { Component, EventEmitter, Input, OnInit, Output } from '@angular/core';
import {
  AdapterDataType,
  AdapterHttpService,
  NodeSourceType,
  SourceSinkNode
} from '../adapter-http.service';
import { NodeClickEvent, TreeNodeWithUiInfo } from '../node-click/node-click';
import { Utils } from '../utils/utils';

@Component({
  selector: 'hd-node-search',
  templateUrl: './node-search.component.html',
  styleUrls: ['./node-search.component.scss'],
  standalone: false
})
export class NodeSearchComponent implements OnInit {
  @Input()
  sourcesOrSinks: SourceSinkNode[] = [];

  @Input()
  searchText = '';

  @Input()
  nodeSourceType!: NodeSourceType;

  @Output()
  nodeClick = new EventEmitter<NodeClickEvent>();

  @Output()
  nodeMetaDataClick = new EventEmitter<NodeClickEvent>();

  ngOnInit(): void {
    Utils.assert(this.nodeSourceType, 'input node source type is missing');
  }

  _nodeClick(sourceSinkNode: SourceSinkNode, event: MouseEvent): void {
    const node: TreeNodeWithUiInfo = {
      id: sourceSinkNode.id,
      name: sourceSinkNode.name,
      parentId: null,
      thingNodeId: sourceSinkNode.thingNodeId,
      type: sourceSinkNode.type,
      filters: sourceSinkNode.filters,
      metadataKey: sourceSinkNode.metadataKey,
      expandable: false,
      level: 0,
      loading: false
    };

    this.nodeClick.emit({
      node,
      event
    });
  }

  _nodeMetaDataClick(sourceSinkNode: SourceSinkNode, event: MouseEvent): void {
    event.preventDefault();
    event.stopPropagation();

    const node: TreeNodeWithUiInfo = {
      id: sourceSinkNode.id,
      name: sourceSinkNode.name,
      parentId: null,
      thingNodeId: sourceSinkNode.thingNodeId,
      type: sourceSinkNode.type,
      filters: sourceSinkNode.filters,
      metadataKey: sourceSinkNode.metadataKey,
      expandable: false,
      level: 0,
      loading: false
    };

    this.nodeMetaDataClick.emit({
      event,
      node,
      nodeSourceType: this._nodeSourceType(node)
    });
  }

  private _nodeSourceType(node: TreeNodeWithUiInfo): NodeSourceType {
    const thingNodeSourceType: NodeSourceType = 'THINGNODE';
    return Utils.isDefined(node.type)
      ? this.nodeSourceType
      : thingNodeSourceType;
  }

  _getTypeColor(type: AdapterDataType | null): string {
    if (Utils.isNullOrUndefined(type)) {
      return '';
    }
    return `var(--${AdapterHttpService.getIOTypeFromAdapterType(type)}-color)`;
  }
}
