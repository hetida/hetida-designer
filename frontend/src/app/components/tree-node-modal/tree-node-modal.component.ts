import { Component, Inject, OnInit } from '@angular/core';
import { MatDialogRef, MAT_DIALOG_DATA } from '@angular/material/dialog';
import { IOType } from 'hetida-flowchart';
import { Subject } from 'rxjs';
import {
  DataSourceSink,
  ThingNodes
} from 'src/app/service/http-service/adapter-http.service';
import {
  TreeNodeItemClickEvent,
  TreeNodeSourceType
} from '../tree-node/tree-node.component';

export interface AdapterTreeModalData {
  thingNodes: ThingNodes[];
  sourcesOrSinks: DataSourceSink[];
  dataSourceType: TreeNodeSourceType;
  initialDataTypeFilter?: IOType;
}

@Component({
  selector: 'hd-tree-node-modal',
  templateUrl: './tree-node-modal.component.html',
  styleUrls: ['./tree-node-modal.component.scss']
})
export class TreeNodeModalComponent implements OnInit {
  public readonly dataSourceSelect = new Subject<TreeNodeItemClickEvent>();

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

  public nodeClick(event: TreeNodeItemClickEvent): void {
    this.dataSourceSelect.next(event);
  }
}
