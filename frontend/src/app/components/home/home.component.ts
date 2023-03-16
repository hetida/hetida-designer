import { ComponentPortal } from '@angular/cdk/portal';
import { HttpClient } from '@angular/common/http';
import { Component, OnInit } from '@angular/core';
import { Store } from '@ngrx/store';
import { combineLatest, Observable } from 'rxjs';
import { map } from 'rxjs/operators';
import { BaseItemType } from 'src/app/enums/base-item-type';
import { RevisionState } from 'src/app/enums/revision-state';
import { BaseItem } from 'src/app/model/base-item';
import { BaseItemActionService } from 'src/app/service/base-item/base-item-action.service';
import { ConfigService } from '../../service/configuration/config.service';
import { ContextMenuService } from 'src/app/service/context-menu/context-menu.service';
import { LocalStorageService } from 'src/app/service/local-storage/local-storage.service';
import { IAppState } from 'src/app/store/app.state';
import { selectHashedAbstractBaseItemLookupById } from 'src/app/store/base-item/base-item.selectors';
import { Utils } from 'src/app/utils/utils';
import { TabItemService } from '../../service/tab-item/tab-item.service';
import { BaseItemContextMenuComponent } from '../base-item-context-menu/base-item-context-menu.component';

@Component({
  selector: 'hd-home',
  templateUrl: './home.component.html',
  styleUrls: ['./home.component.scss']
})
export class HomeComponent implements OnInit {
  constructor(
    private readonly localStorageService: LocalStorageService,
    private readonly store: Store<IAppState>,
    private readonly baseItemActionService: BaseItemActionService,
    private readonly tabItemService: TabItemService,
    private readonly contextMenuService: ContextMenuService,
    private readonly httpClient: HttpClient,
    private readonly configService: ConfigService
  ) {}

  public lastOpened: Observable<BaseItem[]>;
  public version: string;
  public _userInfoText: string;

  ngOnInit() {
    this.httpClient
      .get<string>('assets/VERSION', { responseType: 'text' as 'json' })
      .subscribe((version: string) => {
        this.version = version;
      });
    this.lastOpened = combineLatest([
      this.localStorageService.notifier,
      this.store.select(selectHashedAbstractBaseItemLookupById)
    ]).pipe(
      map(([_, abstractBaseItemsLookup]) => {
        const lastOpenedBaseItemIds: string[] =
          this.localStorageService.getItem('last-opened') ?? [];

        return lastOpenedBaseItemIds
          .filter(() => !Utils.object.isEmpty(abstractBaseItemsLookup))
          .map(baseItemId => abstractBaseItemsLookup[baseItemId])
          .filter(
            (abstractBaseItem): abstractBaseItem is BaseItem =>
              Utils.isDefined(abstractBaseItem) &&
              abstractBaseItem.state !== RevisionState.DISABLED
          );
      })
    );
    this.configService.getConfig().subscribe(config => {
      this._userInfoText = config.userInfoText;
    });
  }

  get lastOpenedWorkflows() {
    return this.lastOpened.pipe(
      map(abstractBaseItems => {
        return abstractBaseItems.filter(
          baseItem => baseItem.type === BaseItemType.WORKFLOW
        );
      })
    );
  }

  get lastOpenedComponents() {
    return this.lastOpened.pipe(
      map(abstractBaseItems => {
        return abstractBaseItems.filter(
          baseItem => baseItem.type === BaseItemType.COMPONENT
        );
      })
    );
  }

  select(selectedItem: BaseItem) {
    this.tabItemService.addBaseItemTab(selectedItem.id);
  }

  openBaseItemContextMenu(selectedItem: BaseItem, mouseEvent: MouseEvent) {
    const { componentPortalRef } = this.contextMenuService.openContextMenu(
      new ComponentPortal(BaseItemContextMenuComponent),
      {
        x: mouseEvent.clientX,
        y: mouseEvent.clientY
      }
    );

    componentPortalRef.instance.baseItem = selectedItem;
  }

  newWorkflow(): void {
    this.baseItemActionService.newWorkflow();
  }

  newComponent(): void {
    this.baseItemActionService.newComponent();
  }
}
