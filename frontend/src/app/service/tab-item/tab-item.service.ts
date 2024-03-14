import { Injectable } from '@angular/core';
import { TransformationService } from '../transformation/transformation.service';
import { TabItem, TabItemType } from '../../model/tab-item';
import { Store } from '@ngrx/store';
import { IAppState } from '../../store/app.state';
import {
  addTabItem,
  unsetActiveTabItem
} from '../../store/tab-item/tab-item.actions';
import { LocalStorageService } from '../local-storage/local-storage.service';
import { Transformation } from '../../model/transformation';
import { QueryParameterService } from '../query-parameter/query-parameter.service';

@Injectable({
  providedIn: 'root'
})
export class TabItemService {
  constructor(
    private readonly store: Store<IAppState>,
    private readonly transformationService: TransformationService,
    private readonly localStorageService: LocalStorageService,
    private readonly queryParameterService: QueryParameterService
  ) {}

  addTransformationTab(transformationId: string): void {
    this.addTabItem({
      transformationId,
      tabItemType: TabItemType.TRANSFORMATION
    });
    this.queryParameterService.addQueryParameter(transformationId);
  }

  addDocumentationTab(
    transformationId: string,
    initialDocumentationEditMode: boolean
  ) {
    this.addTabItem({
      transformationId,
      tabItemType: TabItemType.DOCUMENTATION,
      initialDocumentationEditMode
    });
  }

  deselectActiveTabItem() {
    this.store.dispatch(unsetActiveTabItem());
  }

  createTransformationAndOpenInNewTab(transformation: Transformation): void {
    this.transformationService.createTransformation(transformation).subscribe({
      complete: () => {
        this.addTransformationTab(transformation.id);
      }
    });
  }

  private addTabItem(partialTabItem: Omit<TabItem, 'id'>): void {
    this.store.dispatch(addTabItem(partialTabItem));
    this.localStorageService.addToLastOpened(partialTabItem.transformationId);
  }
}
