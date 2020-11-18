import { CollectionViewer, DataSource } from '@angular/cdk/collections';
import { FlatTreeControl } from '@angular/cdk/tree';
import { BehaviorSubject, merge, Observable } from 'rxjs';
import { map } from 'rxjs/operators';
import {
  ThingConverter,
  TreeNode,
  TreeNodeWithLevelAndExpandableInfo
} from './thing-converter';

export class ThingDatasource<T extends TreeNode> extends DataSource<
  TreeNodeWithLevelAndExpandableInfo<T>
> {
  private readonly flattenedData = new BehaviorSubject<
    TreeNodeWithLevelAndExpandableInfo<T>[]
  >([]);

  private readonly expandedData = new BehaviorSubject<
    TreeNodeWithLevelAndExpandableInfo<T>[]
  >([]);

  // tslint:disable-next-line: variable-name
  _data: BehaviorSubject<T[]>;
  get data() {
    return this._data.value;
  }
  set data(value: T[]) {
    this._data.next(value);
    this.flattenedData.next(this.treeFlattener.flattenNodes(this.data));
    this.treeControl.dataNodes = this.flattenedData.value;
  }

  constructor(
    private readonly treeControl: FlatTreeControl<
      TreeNodeWithLevelAndExpandableInfo<T>
    >,
    private readonly treeFlattener: ThingConverter<T>,
    initialData: T[] = []
  ) {
    super();
    this._data = new BehaviorSubject<T[]>(initialData);
  }

  connect(
    _: CollectionViewer
  ): Observable<TreeNodeWithLevelAndExpandableInfo<T>[]> {
    const changes = [
      this.treeControl.expansionModel.changed,
      this.flattenedData
    ];
    return merge(...changes).pipe(
      map(() => {
        this.expandedData.next(
          this.treeFlattener.expandFlattenedNodes(
            this.flattenedData.value,
            this.treeControl
          )
        );
        return this.expandedData.value;
      })
    );
  }

  disconnect() {
    // no op
  }
}
