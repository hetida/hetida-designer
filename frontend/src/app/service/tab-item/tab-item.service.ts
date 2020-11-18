import { Injectable } from '@angular/core';
import { BaseItemService } from '../base-item/base-item.service';
import { TabItem, TabItemType } from '../../model/tab-item';
import { Store } from '@ngrx/store';
import { IAppState } from '../../store/app.state';
import {
  addTabItem,
  unsetActiveTabItem
} from '../../store/tab-item/tab-item.actions';
import { AbstractBaseItem } from '../../model/base-item';
import { LocalStorageService } from '../local-storage/local-storage.service';

@Injectable({
  providedIn: 'root'
})
export class TabItemService {
  constructor(
    private readonly store: Store<IAppState>,
    private readonly baseItemService: BaseItemService,
    private readonly localStorageService: LocalStorageService
  ) {}

  addTabItem(partialTabItem: Omit<TabItem, 'id'>): void {
    // Loads the fully expanded component or workflow state of a base
    // item when a new tab is added to the state. The tab will only
    // be committed to the state once the expanded base item is in
    // the store. This ensures that the state will already be fully
    // consistent and complete when the tab is being rendered for the
    // first time.
    this.baseItemService.ensureBaseItem(partialTabItem.baseItemId).subscribe({
      complete: () => {
        this.store.dispatch(addTabItem(partialTabItem));
        this.localStorageService.addToLastOpened(partialTabItem.baseItemId);
      }
    });
  }

  addBaseItemTab(baseItemId: string): void {
    this.addTabItem({ baseItemId, tabItemType: TabItemType.BASE_ITEM });
  }

  addDocumentationTab(
    baseItemId: string,
    initialDocumentationEditMode: boolean
  ) {
    this.addTabItem({
      baseItemId,
      tabItemType: TabItemType.DOCUMENTATION,
      initialDocumentationEditMode
    });
  }

  deselectActiveBaseItem() {
    this.store.dispatch(unsetActiveTabItem());
  }

  createBaseItemAndOpenInNewTab(abstractBaseItem: AbstractBaseItem): void {
    this.baseItemService.createBaseItem(abstractBaseItem).subscribe({
      complete: () => {
        this.addBaseItemTab(abstractBaseItem.id);
      }
    });
  }
}
