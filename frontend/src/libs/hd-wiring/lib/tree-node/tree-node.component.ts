import { FlatTreeControl } from '@angular/cdk/tree';
import { Component, EventEmitter, Input, OnInit, Output } from '@angular/core';
import { FormBuilder, FormGroup } from '@angular/forms';
import { IOType } from 'hetida-flowchart';
import { combineLatest, Observable, of } from 'rxjs';
import { debounceTime, switchMap, tap, withLatestFrom } from 'rxjs/operators';
import {
  AdapterDataType,
  AdapterHttpService,
  DataStructureType,
  NodeSourceType,
  SourceSinkNode
} from '../adapter-http.service';
import { NodeClickEvent, TreeNodeWithUiInfo } from '../node-click/node-click';
import { Utils } from '../utils/utils';
import { ThingDataSource } from './thing-datasource';

@Component({
  selector: 'hd-tree-node',
  templateUrl: './tree-node.component.html',
  styleUrls: ['./tree-node.component.scss'],
  standalone: false
})
export class TreeNodeComponent implements OnInit {
  nodeSearchResult: SourceSinkNode[] = [];

  treeControl = new FlatTreeControl<TreeNodeWithUiInfo>(
    node => node.level,
    node => node.expandable
  );

  dataSource!: ThingDataSource;

  @Input()
  initialDataTypeFilter: IOType | undefined = undefined;

  @Input()
  initialTextSearchFilter = '';

  @Input()
  nodeSourceType!: NodeSourceType;

  @Input()
  adapterUrl!: string;

  @Output()
  nodeClick = new EventEmitter<NodeClickEvent>();

  @Output()
  nodeMetaDataClick = new EventEmitter<NodeClickEvent>();

  public filterFormGroup: FormGroup = this.formBuilder.group({
    textSearch: '',
    dataTypeSearch: null
  });

  constructor(
    private readonly formBuilder: FormBuilder,
    private readonly adapterService: AdapterHttpService
  ) {}

  get ioType(): Record<string, string> {
    return IOType;
  }

  ngOnInit(): void {
    Utils.assert(this.adapterUrl, 'adapter url is missing');
    Utils.assert(
      this.nodeSourceType,
      'nodeSourceType should be one of "source" or "sink"'
    );

    this.dataSource = new ThingDataSource(
      this.treeControl,
      this.adapterUrl,
      this.adapterService,
      this.nodeSourceType
    );
    const textSearchForm = this.filterFormGroup.get('textSearch');
    const typeSearchForm = this.filterFormGroup.get('dataTypeSearch');

    Utils.assert(typeSearchForm);
    Utils.assert(textSearchForm);

    const debouncedTextSearch$ = textSearchForm.valueChanges.pipe(
      debounceTime(500)
    );

    const typeSearchForm$ = typeSearchForm.valueChanges.pipe(
      tap(typeSearch => this.dataSource.setIoTypeFilter(typeSearch))
    );

    combineLatest([debouncedTextSearch$, typeSearchForm$])
      .pipe(
        switchMap(([textSearch]) => {
          if (Utils.string.isEmptyOrUndefined(textSearch)) {
            return of([] as SourceSinkNode[]);
          }
          const payload = {
            adapterUrl: this.adapterUrl,
            stringFilter: textSearch
          };

          let sourceOrSink$: Observable<SourceSinkNode[]>;
          if (this.nodeSourceType === 'SINK') {
            sourceOrSink$ = this.adapterService.getSinks(payload);
          } else if (this.nodeSourceType === 'SOURCE') {
            sourceOrSink$ = this.adapterService.getSources(payload);
          } else {
            throw Error(
              `no search api provided for ${this.nodeSourceType} node source type.`
            );
          }
          return sourceOrSink$;
        })
      )
      .pipe(withLatestFrom(typeSearchForm$))
      .subscribe(([sourcesOrSinks, typeSearch]) => {
        if (Utils.isNullOrUndefined(typeSearch)) {
          this.nodeSearchResult = sourcesOrSinks;
        } else {
          this.nodeSearchResult = AdapterHttpService.filterNodesByIoType(
            sourcesOrSinks,
            typeSearch
          );
        }
      });

    textSearchForm.setValue(this.initialTextSearchFilter);
    typeSearchForm.setValue(this.initialDataTypeFilter);
  }

  expandAll(): void {
    this.treeControl.expandAll();
  }

  collapseAll(): void {
    this.treeControl.collapseAll();
  }

  _searchNodeClick(event: NodeClickEvent): void {
    this.nodeClick.emit(event);
  }

  _nodeClick(node: TreeNodeWithUiInfo, event: MouseEvent): void {
    const adapterDataType = node.type;
    let nodeSourceType: NodeSourceType | undefined = this.nodeSourceType;
    if (
      Utils.isDefined(adapterDataType) &&
      adapterDataType.includes(DataStructureType.METADATA)
    ) {
      nodeSourceType = 'THINGNODE';
    }
    this.nodeClick.emit({
      node,
      event,
      nodeSourceType,
      adapterUrl: this.adapterUrl
    });
  }

  _nodeMetaDataClick(node: TreeNodeWithUiInfo, event: MouseEvent): void {
    this.nodeMetaDataClick.emit({
      node,
      event,
      nodeSourceType: this._nodeSourceType(node),
      adapterUrl: this.adapterUrl
    });
  }

  _searchNodeMetaDataClick(event: NodeClickEvent): void {
    this.nodeMetaDataClick.emit(event);
  }

  private _nodeSourceType(node: TreeNodeWithUiInfo): NodeSourceType {
    const thingNodeSourceType: NodeSourceType = 'THINGNODE';
    return Utils.isDefined(node.type)
      ? this.nodeSourceType
      : thingNodeSourceType;
  }

  _isSearchViewVisible(): boolean {
    const textSearchForm = this.filterFormGroup.get('textSearch');
    Utils.assert(textSearchForm);
    return !Utils.string.isEmptyOrUndefined(textSearchForm.value);
  }

  _searchText(): string {
    const textSearchForm = this.filterFormGroup.get('textSearch');
    Utils.assert(textSearchForm);
    return Utils.string.isEmptyOrUndefined(textSearchForm.value)
      ? ''
      : textSearchForm.value;
  }

  _getTypeColor(type: AdapterDataType | null): string {
    if (Utils.isNullOrUndefined(type)) {
      return '';
    }
    return `var(--${AdapterHttpService.getIOTypeFromAdapterType(type)}-color)`;
  }
}
