import { COMMA, ENTER } from '@angular/cdk/keycodes';
import { FlatTreeControl } from '@angular/cdk/tree';
import {
  ChangeDetectionStrategy,
  ChangeDetectorRef,
  Component,
  EventEmitter,
  Input,
  OnInit,
  Output
} from '@angular/core';
import { FormBuilder, FormGroup } from '@angular/forms';
import { MatChipInputEvent } from '@angular/material/chips';
import { IOType } from 'hetida-flowchart';
import { combineLatest } from 'rxjs';
import { AdapterUiFlatNode } from 'src/app/model/adapter-ui-node';
import {
  DataSourceSink,
  ThingNodes
} from 'src/app/service/http-service/adapter-http.service';
import { Immutable } from 'src/app/utils/Immutable';
import { Utils } from 'src/app/utils/utils';
import { ThingConverter } from './thing-converter';
import { ThingDatasource } from './thing-datasource';

export type TreeNodeSourceType = 'source' | 'sink';

export interface TreeNodeItemClickEvent {
  node: AdapterUiFlatNode;
  event: MouseEvent;
  dataSourceType: TreeNodeSourceType;
}

@Component({
  selector: 'hd-tree-node',
  templateUrl: './tree-node.component.html',
  styleUrls: ['./tree-node.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush
})
export class TreeNodeComponent implements OnInit {
  readonly separatorKeysCodes: number[] = [ENTER, COMMA];

  treeControl = new FlatTreeControl<AdapterUiFlatNode>(
    node => node.level,
    node => node.expandable
  );

  dataSource: ThingDatasource<AdapterUiFlatNode>;
  private thingConverter: ThingConverter<AdapterUiFlatNode>;
  private thingNodeCp: ThingNodes[];

  @Input()
  initialDataTypeFilter: IOType | null = null;

  @Input()
  initalTextSearchPartsFilter: string[] = [];

  @Input()
  thingNodes: ThingNodes[];

  @Input()
  sourcesOrSinks: DataSourceSink[];

  @Input()
  dataSourceType: TreeNodeSourceType;

  @Output()
  nodeClick = new EventEmitter<TreeNodeItemClickEvent>();

  public filterFormGroup: FormGroup = this.formBuilder.group({
    textSearchParts: [[]],
    dataTypeSearch: null
  });

  constructor(
    private readonly formBuilder: FormBuilder,
    private readonly changeDetector: ChangeDetectorRef
  ) {}

  get ioType(): Record<string, string> {
    return IOType;
  }

  ngOnInit() {
    this.thingNodeCp = this.thingNodes.map(thingNode => ({ ...thingNode }));
    this.thingConverter = new ThingConverter(this.sourcesOrSinks);
    this.dataSource = new ThingDatasource<AdapterUiFlatNode>(
      this.treeControl,
      this.thingConverter
    );

    this.dataSource.data = (this.thingNodeCp as unknown) as AdapterUiFlatNode[]; // TODO

    if (Utils.isNullOrUndefined(this.dataSourceType)) {
      throw Error('dataSourceType should be one of "source" or "sink"');
    }
    const typeSearch$ = this.filterFormGroup.get('dataTypeSearch')
      ?.valueChanges;
    const textSearchParts$ = this.filterFormGroup.get('textSearchParts')
      ?.valueChanges;

    Utils.assert(typeSearch$);
    Utils.assert(textSearchParts$);

    combineLatest([typeSearch$, textSearchParts$]).subscribe(
      ([typeSearch, textSearchParts]) => {
        let filteredSouresOrSinks = this.sourcesOrSinks;

        if (typeof typeSearch === 'string') {
          filteredSouresOrSinks = filteredSouresOrSinks.filter(s =>
            s.dataType.toLowerCase().includes(typeSearch.toLowerCase())
          );
        }

        this.thingConverter = new ThingConverter(
          filteredSouresOrSinks,
          textSearchParts
        );
        this.dataSource = new ThingDatasource<AdapterUiFlatNode>(
          this.treeControl,
          this.thingConverter
        );
        this.dataSource.data = (this
          .thingNodeCp as unknown) as AdapterUiFlatNode[];
        this.treeControl.expandAll();
        this.changeDetector.detectChanges();
      }
    );

    this.filterFormGroup
      .get('textSearchParts')
      ?.setValue(this.initalTextSearchPartsFilter);
    this.filterFormGroup
      .get('dataTypeSearch')
      ?.setValue(this.initialDataTypeFilter);

    this.changeDetector.detectChanges();
  }

  expandAll() {
    this.treeControl.expandAll();
  }

  collapseAll() {
    this.treeControl.collapseAll();
  }

  _nodeClick(node: AdapterUiFlatNode, event: MouseEvent) {
    this.nodeClick.emit({
      node,
      event,
      dataSourceType: this.dataSourceType
    });
  }

  public getTypeColor(type: string | null): string {
    if (typeof type === 'string') {
      // check for series type
      if (type.toLowerCase().includes('series')) {
        return `var(--${IOType.SERIES}-color)`;
      }
      return `var(--${type.toUpperCase()}-color)`;
    }
    return '';
  }

  add(event: MatChipInputEvent): void {
    const input = event.input;
    const value = event.value;

    if ((value ?? '').trim() !== '') {
      this.filterFormGroup
        .get('textSearchParts')
        ?.setValue(
          Immutable.push(
            this.filterFormGroup.get('textSearchParts')?.value,
            value
          )
        );
    }

    input.value = '';
  }

  remove(node: string): void {
    const index = this.filterFormGroup
      .get('textSearchParts')
      ?.value.indexOf(node);

    if (index >= 0) {
      this.filterFormGroup
        .get('textSearchParts')
        ?.setValue(
          Immutable.delete(
            this.filterFormGroup.get('textSearchParts')?.value,
            index
          )
        );
    }
  }
}
