import { Component, OnDestroy, OnInit } from '@angular/core';
import { MatTabChangeEvent } from '@angular/material/tabs';
import { createSelector, Store } from '@ngrx/store';
import { Subject } from 'rxjs';
import { takeUntil } from 'rxjs/operators';
import { PopoverService } from 'src/app/service/popover/popover.service';
import { setExecutionProtocol } from 'src/app/store/execution-protocol/execution-protocol.actions';
import {
  removeTabItem,
  setActiveTabItem,
  unsetActiveTabItem
} from 'src/app/store/tab-item/tab-item.actions';
import { TransformationType } from '../../enums/transformation-type';
import { TabItem, TabItemType } from '../../model/tab-item';
import { IAppState } from '../../store/app.state';
import {
  selectActiveTabItem,
  selectOrderedTabItemsWithTransformation,
  TabItemWithTransformation
} from '../../store/tab-item/tab-item.selectors';
import { isComponentTransformation } from '../../model/transformation';
import { selectAllTransformations } from 'src/app/store/transformation/transformation.selectors';
import { QueryParameterService } from 'src/app/service/query-parameter/query-parameter.service';
import { TabItemService } from 'src/app/service/tab-item/tab-item.service';
import { NotificationService } from 'src/app/service/notifications/notification.service';

const HOME_TAB = 0;

const getTabItemHash = (
  tabItemWithTransformation: TabItemWithTransformation
): string => {
  return `${tabItemWithTransformation.transformation.id}-${tabItemWithTransformation.tabItemType}`;
};

interface ContentViewStoreState {
  orderedTabItemsWithTransformation: TabItemWithTransformation[];
  activeTabItem: TabItem;
}

// This selector is not generally re-usable but use case
// specific, so we keep it co-located with the component.
export const selectContentViewStoreState = createSelector(
  selectOrderedTabItemsWithTransformation,
  selectActiveTabItem,
  (
    orderedTabItemsWithTransformation,
    activeTabItem
  ): ContentViewStoreState => ({
    orderedTabItemsWithTransformation,
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
  readonly _ItemType = TransformationType;

  // Component State
  _selectedTabIndex = 0;

  // ngrx State
  _tabItems: TabItemWithTransformation[] = [];

  isComponentTransformation: typeof isComponentTransformation =
    isComponentTransformation;

  constructor(
    private readonly store: Store<IAppState>,
    private readonly popoverService: PopoverService,
    private readonly queryParameterService: QueryParameterService,
    private readonly tabItemService: TabItemService,
    private readonly notificationService: NotificationService
  ) {}

  private readonly _ngOnDestroyNotify = new Subject<void>();

  ngOnDestroy(): void {
    this._ngOnDestroyNotify.next();
    this._ngOnDestroyNotify.complete();
  }

  ngOnInit() {
    this.store
      .select(selectContentViewStoreState)
      .pipe(takeUntil(this._ngOnDestroyNotify))
      .subscribe(({ orderedTabItemsWithTransformation, activeTabItem }) => {
        this._tabItems = orderedTabItemsWithTransformation;

        const selectedTabItemIndex =
          activeTabItem === null ||
          orderedTabItemsWithTransformation.length === 0
            ? HOME_TAB
            : orderedTabItemsWithTransformation.findIndex(
                tabItem =>
                  tabItem.transformation.id ===
                    activeTabItem.transformationId &&
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

    this.addTabsFromQueryParameters();
  }

  _trackBy(
    _: number,
    tabItemWithTransformation: TabItemWithTransformation
  ): string {
    return getTabItemHash(tabItemWithTransformation);
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

  _isDocumentation(tabItem: TabItemWithTransformation): boolean {
    return tabItem.tabItemType === TabItemType.DOCUMENTATION;
  }

  _isTransformation(tabItem: TabItemWithTransformation): boolean {
    return tabItem.tabItemType === TabItemType.TRANSFORMATION;
  }

  _onTabClose(tabItemToClose: TabItemWithTransformation) {
    this.popoverService.closePopover();
    this.store.dispatch(removeTabItem(tabItemToClose.id));

    if (tabItemToClose.tabItemType === TabItemType.TRANSFORMATION) {
      this.queryParameterService.deleteQueryParameter(
        tabItemToClose.transformation.id
      );
    }
  }

  _closePopover(): void {
    this.popoverService.closePopover();
  }

  private async addTabsFromQueryParameters(): Promise<void> {
    const transformationsNotify$ = new Subject<void>();
    const ids = await this.queryParameterService.getIdsFromQueryParameters();

    this.store
      .select(selectAllTransformations)
      .pipe(takeUntil(transformationsNotify$))
      .subscribe(transformations => {
        for (const id of ids) {
          if (
            transformations.find(transformation => transformation.id === id) !==
            undefined
          ) {
            this.tabItemService.addTransformationTab(id);
            // ngOnInit runs two times, on the first run the store is always empty, so we ignore missing transformations
          } else if (transformations.length > 0) {
            // only the first missing transformation triggers an pop-up message
            this.notificationService.warn(
              'Could not find transformation, see console for details.'
            );
            // to look after all missing transformations
            console.warn(`Could not find transformation with id '${id}'`);
          }
        }

        // closing the store subscription after getting transformations, to prevent re-trigger on store changes
        if (transformations.length > 0) {
          transformationsNotify$.next();
          transformationsNotify$.complete();
        }
      });
  }
}
