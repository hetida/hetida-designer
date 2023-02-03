import { Injectable } from '@angular/core';
import { BaseItemService } from '../base-item/base-item.service';
import { TabItem, TabItemType } from '../../model/tab-item';
import { Store } from '@ngrx/store';
import { IAppState } from '../../store/app.state';
import {
  addTabItem,
  unsetActiveTabItem
} from '../../store/tab-item/tab-item.actions';
import { LocalStorageService } from '../local-storage/local-storage.service';
import { Transformation } from '../../model/transformation';

@Injectable({
  providedIn: 'root'
})
export class TabItemService {
  constructor(
    private readonly store: Store<IAppState>,
    private readonly baseItemService: BaseItemService,
    private readonly localStorageService: LocalStorageService
  ) {}

  addTransformationTab(transformationId: string): void {
    this.addTabItem({
      transformationId,
      tabItemType: TabItemType.BASE_ITEM
    });
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
    this.baseItemService.createTransformation(transformation).subscribe({
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
