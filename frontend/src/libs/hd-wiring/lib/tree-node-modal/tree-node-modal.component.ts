import { Component, Inject, OnInit } from '@angular/core';
import { MatDialogRef, MAT_DIALOG_DATA } from '@angular/material/dialog';
import { IOType } from 'hetida-flowchart';
import { Subject } from 'rxjs';
import { NodeSourceType } from '../adapter-http.service';
import { NodeClickEvent } from '../node-click/node-click';
import { Utils } from '../utils/utils';

export interface AdapterTreeModalData {
  nodeSourceType: NodeSourceType;
  initialDataTypeFilter?: IOType;
  adapterUrl: string;
}

@Component({
  selector: 'hd-tree-node-modal',
  templateUrl: './tree-node-modal.component.html',
  styleUrls: ['./tree-node-modal.component.scss'],
  standalone: false
})
export class TreeNodeModalComponent implements OnInit {
  public readonly nodeClick = new Subject<NodeClickEvent>();
  public readonly nodeMetaDataClick = new Subject<NodeClickEvent>();

  constructor(
    public dialogRef: MatDialogRef<TreeNodeModalComponent>,
    @Inject(MAT_DIALOG_DATA) public data: AdapterTreeModalData
  ) {}

  ngOnInit(): void {}

  public onCancel(): void {
    this.dialogRef.close();
  }

  public onOk(): void {
    this.dialogRef.close();
  }

  _nodeClick(event: NodeClickEvent): void {
    const eventWithSourceTypeInfo: NodeClickEvent = {
      ...event,
      nodeSourceType: Utils.isDefined(event.nodeSourceType)
        ? event.nodeSourceType
        : this.data.nodeSourceType,
      adapterUrl: this.data.adapterUrl
    };
    this.nodeClick.next(eventWithSourceTypeInfo);
  }

  _nodeMetaDataClick(event: NodeClickEvent): void {
    const eventWithSourceTypeInfo: NodeClickEvent = {
      ...event,
      adapterUrl: this.data.adapterUrl
    };
    this.nodeMetaDataClick.next(eventWithSourceTypeInfo);
  }
}
