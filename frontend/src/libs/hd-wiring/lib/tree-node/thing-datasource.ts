import {
  CollectionViewer,
  DataSource,
  SelectionChange
} from '@angular/cdk/collections';
import { FlatTreeControl } from '@angular/cdk/tree';
import { IOType } from 'hetida-flowchart';
import {
  BehaviorSubject,
  lastValueFrom,
  merge,
  Observable,
  Subscription
} from 'rxjs';
import { map } from 'rxjs/operators';
import { AdapterHttpService, NodeSourceType } from '../adapter-http.service';
import { TreeNodeWithUiInfo } from '../node-click/node-click';
import { Immutable } from '../utils/Immutable';
import { ThingConverter } from './thing-converter';

/**
 * Responsible of loading tree node data. On initialization, root elements will be loaded automatically.
 */
export class ThingDataSource extends DataSource<TreeNodeWithUiInfo> {
  private _subscriptions: Subscription[] = [];
  private _isLoadingInitialData = true;
  private _originalData: TreeNodeWithUiInfo[] = [];
  get isLoadingInitialData() {
    return this._isLoadingInitialData;
  }
  _data: BehaviorSubject<TreeNodeWithUiInfo[]>;
  get data(): TreeNodeWithUiInfo[] {
    return this._data.value;
  }
  set data(value: TreeNodeWithUiInfo[]) {
    this._originalData = [...value];
    const filteredData = AdapterHttpService.filterNodesByIoType(
      this._originalData,
      this._ioTypeFilter
    );
    this._data.next(filteredData);
    this.treeControl.dataNodes = filteredData;
  }
  private _ioTypeFilter: IOType | undefined;

  constructor(
    private readonly treeControl: FlatTreeControl<TreeNodeWithUiInfo>,
    private readonly adapterUrl: string,
    private readonly adapterService: AdapterHttpService,
    private readonly nodeSourceType: NodeSourceType,
    initialData: TreeNodeWithUiInfo[] = []
  ) {
    super();
    this._data = new BehaviorSubject<TreeNodeWithUiInfo[]>(initialData);
  }

  connect(_: CollectionViewer): Observable<TreeNodeWithUiInfo[]> {
    // load initial data
    this._loadInitialData();
    const changes = [this.treeControl.expansionModel.changed, this._data];

    this._subscriptions.push(
      this.treeControl.expansionModel.changed.subscribe(change => {
        if (change.added || change.removed) {
          this._handleTreeControl(change);
        }
      })
    );

    return merge(...changes).pipe(map(() => this.data));
  }

  disconnect() {
    this.data = [];
    this._subscriptions.forEach(subscription => subscription.unsubscribe());
    this._subscriptions = [];
  }

  /**
   * Filters nodes by type.
   * @param ioTypeFilter null or undefined reset this filter.
   */
  setIoTypeFilter(ioTypeFilter?: IOType) {
    this._ioTypeFilter = ioTypeFilter;
    this.data = this._originalData;
  }

  private async _loadInitialData() {
    const rootNodes = await this._loadChildNodes();
    this.data = rootNodes;
    this._isLoadingInitialData = false;
  }

  private _handleTreeControl(change: SelectionChange<TreeNodeWithUiInfo>) {
    if (change.added) {
      change.added.forEach(node => {
        this._toggleNode(node, true);
      });
    }
    if (change.removed) {
      change.removed.forEach(node => {
        this._toggleNode(node, false);
      });
    }
  }

  private async _toggleNode(parentNode: TreeNodeWithUiInfo, expand: boolean) {
    const index = this._originalData.indexOf(parentNode);
    parentNode.loading = true;
    if (expand) {
      const childNodes = await this._loadChildNodes(parentNode);
      this.data = Immutable.slice(
        index + 1,
        0,
        ...childNodes
      )(this._originalData);
    } else {
      let count = 0;
      for (
        let i = index + 1;
        i < this._originalData.length &&
        this._originalData[i].level > parentNode.level;
        i++, count++
      ) {}
      const empty: TreeNodeWithUiInfo[] = [];
      this.data = Immutable.slice(
        index + 1,
        count,
        ...empty
      )(this._originalData);
    }
    parentNode.loading = false;
  }

  /**
   *
   * @param parentNode if no param is given root nodes will be load
   */
  private async _loadChildNodes(
    parentNode?: TreeNodeWithUiInfo
  ): Promise<TreeNodeWithUiInfo[]> {
    const adapterResponse$ = this.adapterService.getNodesOfAdapter(
      this.adapterUrl,
      parentNode ? parentNode.id : undefined
    );
    const adapterResponse = await lastValueFrom(adapterResponse$);

    const sourcesOrSinks =
      this.nodeSourceType === 'SOURCE'
        ? adapterResponse.sources
        : adapterResponse.sinks;

    const extendedNodes = ThingConverter.addExtendedNodeInformation(
      parentNode ? parentNode.level : 0,
      adapterResponse.thingNodes,
      sourcesOrSinks
    );

    return extendedNodes;
  }
}
