import { Component, OnDestroy, OnInit } from '@angular/core';
import { MatTabChangeEvent } from '@angular/material/tabs';
import { createSelector, Store } from '@ngrx/store';
import { Subject } from 'rxjs';
import { takeUntil } from 'rxjs/operators';
import { PopoverService } from 'src/app/service/popover.service';
import { setExecutionProtocol } from 'src/app/store/execution-protocol/execution-protocol.actions';
import {
  removeTabItem,
  setActiveTabItem,
  unsetActiveTabItem
} from 'src/app/store/tab-item/tab-item.actions';
import { BaseItemType } from '../../enums/base-item-type';
import { TabItem, TabItemType } from '../../model/tab-item';
import { IAppState } from '../../store/app.state';
import {
  selectActiveTabItem,
  selectOrderedTabItemsWithBaseItem,
  TabItemWithBaseItem
} from '../../store/tab-item/tab-item.selectors';

const HOME_TAB = 0;

const getTabItemHash = (tabItemWithBaseItem: TabItemWithBaseItem): string => {
  return `${tabItemWithBaseItem.baseItem.id}-${tabItemWithBaseItem.tabItemType}`;
};

interface ContentViewStoreState {
  orderedTabItemsWithBaseItem: TabItemWithBaseItem[];
  activeTabItem: TabItem;
}

// This selector is not generally re-usable but use case
// specific, so we keep it co-located with the component.
export const selectContentViewStoreState = createSelector(
  selectOrderedTabItemsWithBaseItem,
  selectActiveTabItem,
  (orderedTabItemsWithBaseItem, activeTabItem): ContentViewStoreState => ({
    orderedTabItemsWithBaseItem,
    activeTabItem
  })
);

@Component({
  selector: 'hd-content-view',
  templateUrl: './content-view.component.html',
  styleUrls: ['./content-view.component.scss']
})
export class ContentViewComponent implements OnInit, OnDestroy {
  // Constants
  readonly _ItemType = BaseItemType;

  // Component State
  _selectedTabIndex = 0;

  // ngrx State
  _tabItems: TabItemWithBaseItem[] = [];

  constructor(
    private readonly store: Store<IAppState>,
    private readonly popoverService: PopoverService
  ) {}

  private readonly _ngOnDestroyNotify = new Subject();
  ngOnDestroy(): void {
    this._ngOnDestroyNotify.next();
    this._ngOnDestroyNotify.complete();
  }

  ngOnInit() {
    this.store
      .select(selectContentViewStoreState)
      .pipe(takeUntil(this._ngOnDestroyNotify))
      .subscribe(({ orderedTabItemsWithBaseItem, activeTabItem }) => {
        this._tabItems = orderedTabItemsWithBaseItem;

        const selectedTabItemIndex =
          activeTabItem === null || orderedTabItemsWithBaseItem.length === 0
            ? HOME_TAB
            : orderedTabItemsWithBaseItem.findIndex(
                tabItem =>
                  tabItem.baseItem.id === activeTabItem.baseItemId &&
                  tabItem.tabItemType === activeTabItem.tabItemType
              ) + 1;

        // We may only set the selected tab index once the corresponding
        // material tab component has been rendered. Otherwise the material
        // tab group will not know the index yet and will re-set the index
        // to zero. This is the purpose of postponing the update to the next
        // tick.
        setTimeout(() => {
          this._selectedTabIndex = selectedTabItemIndex;
        }, 0);
      });
  }

  _trackBy(_: number, tabItemWithBaseItem: TabItemWithBaseItem): string {
    return getTabItemHash(tabItemWithBaseItem);
  }

  _onTabChange(event: MatTabChangeEvent) {
    if (event.index === HOME_TAB) {
      this.store.dispatch(unsetActiveTabItem());
    } else {
      if (this._selectedTabIndex !== event.index) {
        this.store.dispatch(
          setActiveTabItem(getTabItemHash(this._tabItems[event.index - 1]))
        );
      }
    }
    this._closePopover();
    this.store.dispatch(setExecutionProtocol());
  }

  _isDocumentation(tabItem: TabItemWithBaseItem): boolean {
    return tabItem.tabItemType === TabItemType.DOCUMENTATION;
  }

  _isBaseItem(tabItem: TabItemWithBaseItem): boolean {
    return tabItem.tabItemType === TabItemType.BASE_ITEM;
  }

  _onTabClose(tabItemToClose: TabItemWithBaseItem) {
    this.popoverService.closePopover();
    this.store.dispatch(removeTabItem(tabItemToClose.id));
  }

  _closePopover(): void {
    this.popoverService.closePopover();
  }
}
