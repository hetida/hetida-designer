import { ComponentPortal } from '@angular/cdk/portal';
import { HttpClient } from '@angular/common/http';
import { Component, OnInit } from '@angular/core';
import { Store } from '@ngrx/store';
import { combineLatest, Observable } from 'rxjs';
import { map } from 'rxjs/operators';
import { BaseItemType } from 'src/app/enums/base-item-type';
import { RevisionState } from 'src/app/enums/revision-state';
import { BaseItem } from 'src/app/model/base-item';
import { Transformation } from 'src/app/model/new-api/transformation';
import { BaseItemActionService } from 'src/app/service/base-item/base-item-action.service';
import { ContextMenuService } from 'src/app/service/context-menu/context-menu.service';
import { LocalStorageService } from 'src/app/service/local-storage/local-storage.service';
import { selectHashedTransformationLookupById } from 'src/app/store/transformation/transformation.selectors';
import { TransformationState } from 'src/app/store/transformation/transformation.state';
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
    private readonly transformationStore: Store<TransformationState>,
    private readonly baseItemActionService: BaseItemActionService,
    private readonly tabItemService: TabItemService,
    private readonly contextMenuService: ContextMenuService,
    private readonly httpClient: HttpClient
  ) {}

  public lastOpened: Observable<Transformation[]>;
  public version: string;

  ngOnInit() {
    this.httpClient
      .get<string>('assets/VERSION', { responseType: 'text' as 'json' })
      .subscribe((version: string) => {
        this.version = version;
      });
    this.lastOpened = combineLatest([
      this.localStorageService.notifier,
      this.transformationStore.select(selectHashedTransformationLookupById)
    ]).pipe(
      map(([_, transformationsLookup]) => {
        const lastOpenedTransformationIds: string[] =
          this.localStorageService.getItem('last-opened') ?? [];

        return lastOpenedTransformationIds
          .filter(() => !Utils.object.isEmpty(transformationsLookup))
          .map(transformationId => transformationsLookup[transformationId])
          .filter(
            (transformation): transformation is Transformation =>
              Utils.isDefined(transformation) &&
              transformation.state !== RevisionState.DISABLED
          );
      })
    );
  }

  get lastOpenedWorkflows() {
    return this.lastOpened.pipe(
      map(transformations => {
        return transformations.filter(
          transformation => transformation.type === BaseItemType.WORKFLOW
        );
      })
    );
  }

  get lastOpenedComponents() {
    return this.lastOpened.pipe(
      map(transformations => {
        return transformations.filter(
          transformation => transformation.type === BaseItemType.COMPONENT
        );
      })
    );
  }

  select(selectedItem: Transformation) {
    this.tabItemService.addTransformationTab(selectedItem.id);
  }

  // TODO Change BaseItemContextMenuComponent to TransformationContextMenuComponent
  openTransformationContextMenu(
    selectedItem: BaseItem,
    mouseEvent: MouseEvent
  ) {
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
