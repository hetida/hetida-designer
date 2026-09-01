import { FlatTreeControl } from '@angular/cdk/tree';
import { Component, EventEmitter, Input, OnInit, Output } from '@angular/core';
import { FormBuilder, FormGroup } from '@angular/forms';
import { IOType } from 'hetida-flowchart';
import { combineLatest, Observable, of } from 'rxjs';
import { debounceTime, switchMap, tap, withLatestFrom } from 'rxjs/operators';
import {
  AdapterDataType,
  AdapterHttpService,
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
  public dataSource!: ThingDataSource;

  public _nodeSearchResult: SourceSinkNode[] = [];

  public _treeControl = new FlatTreeControl<TreeNodeWithUiInfo>(
    node => node.level,
    node => node.expandable
  );

  public _filterFormGroup: FormGroup = this.formBuilder.group({
    textSearch: '',
    dataTypeSearch: null
  });

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

  constructor(
    private readonly formBuilder: FormBuilder,
    private readonly adapterService: AdapterHttpService
  ) {}

  ngOnInit(): void {
    Utils.assert(this.adapterUrl, 'adapter url is missing');
    Utils.assert(
      this.nodeSourceType,
      'nodeSourceType should be one of "source" or "sink"'
    );

    this.dataSource = new ThingDataSource(
      this._treeControl,
      this.adapterUrl,
      this.adapterService,
      this.nodeSourceType
    );
    const textSearchForm = this._filterFormGroup.get('textSearch');
    const typeSearchForm = this._filterFormGroup.get('dataTypeSearch');

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
          this._nodeSearchResult = sourcesOrSinks;
        } else {
          this._nodeSearchResult = AdapterHttpService.filterNodesByIoType(
            sourcesOrSinks,
            typeSearch
          );
        }
      });

    textSearchForm.setValue(this.initialTextSearchFilter);
    typeSearchForm.setValue(this.initialDataTypeFilter);
  }

  public get ioType(): Record<string, string> {
    return IOType;
  }

  public _expandAll(): void {
    this._treeControl.expandAll();
  }

  public _collapseAll(): void {
    this._treeControl.collapseAll();
  }

  public _searchNodeClick(event: NodeClickEvent): void {
    this.nodeClick.emit(event);
  }

  public _nodeClick(node: TreeNodeWithUiInfo, event: MouseEvent): void {
    let nodeSourceType: NodeSourceType | undefined = this.nodeSourceType;
    if (Utils.isDefined(node.metadataKey)) {
      nodeSourceType = 'THINGNODE';
    }
    this.nodeClick.emit({
      node,
      event,
      nodeSourceType,
      adapterUrl: this.adapterUrl
    });
  }

  public _nodeMetaDataClick(node: TreeNodeWithUiInfo, event: MouseEvent): void {
    this.nodeMetaDataClick.emit({
      node,
      event,
      nodeSourceType: this._nodeSourceType(node),
      adapterUrl: this.adapterUrl
    });
  }

  public _searchNodeMetaDataClick(event: NodeClickEvent): void {
    this.nodeMetaDataClick.emit(event);
  }

  private _nodeSourceType(node: TreeNodeWithUiInfo): NodeSourceType {
    const thingNodeSourceType: NodeSourceType = 'THINGNODE';
    return Utils.isDefined(node.type)
      ? this.nodeSourceType
      : thingNodeSourceType;
  }

  public _isSearchViewVisible(): boolean {
    const textSearchForm = this._filterFormGroup.get('textSearch');
    Utils.assert(textSearchForm);
    return !Utils.string.isEmptyOrUndefined(textSearchForm.value);
  }

  public _searchText(): string {
    const textSearchForm = this._filterFormGroup.get('textSearch');
    Utils.assert(textSearchForm);
    return Utils.string.isEmptyOrUndefined(textSearchForm.value)
      ? ''
      : textSearchForm.value;
  }

  public _getTypeColor(type: AdapterDataType | null): string {
    if (Utils.isNullOrUndefined(type)) {
      return '';
    }
    return `var(--${AdapterHttpService.getIOTypeFromAdapterType(type)}-color)`;
  }
}
