import { ComponentPortal } from '@angular/cdk/portal';
import { HttpClient } from '@angular/common/http';
import { Component, OnInit } from '@angular/core';
import { Store } from '@ngrx/store';
import { combineLatest, Observable } from 'rxjs';
import { map } from 'rxjs/operators';
import { TransformationType } from 'src/app/enums/transformation-type';
import { RevisionState } from 'src/app/enums/revision-state';
import { Transformation } from 'src/app/model/transformation';
import { TransformationActionService } from 'src/app/service/transformation/transformation-action.service';
import { ConfigService } from '../../service/configuration/config.service';
import { ContextMenuService } from 'src/app/service/context-menu/context-menu.service';
import { LocalStorageService } from 'src/app/service/local-storage/local-storage.service';
import { selectHashedTransformationLookupById } from 'src/app/store/transformation/transformation.selectors';
import { TransformationState } from 'src/app/store/transformation/transformation.state';
import { Utils } from 'src/app/utils/utils';
import { TabItemService } from '../../service/tab-item/tab-item.service';
import { TransformationContextMenuComponent } from '../transformation-context-menu/transformation-context-menu.component';

@Component({
  selector: 'hd-home-tab',
  templateUrl: './home-tab.component.html',
  styleUrls: ['./home-tab.component.scss']
})
export class HomeTabComponent implements OnInit {
  constructor(
    private readonly localStorageService: LocalStorageService,
    private readonly transformationStore: Store<TransformationState>,
    private readonly transformationActionService: TransformationActionService,
    private readonly tabItemService: TabItemService,
    private readonly contextMenuService: ContextMenuService,
    private readonly httpClient: HttpClient,
    private readonly configService: ConfigService
  ) {}

  public lastOpened: Observable<Transformation[]>;
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
    this.configService.getConfig().subscribe(config => {
      this._userInfoText = config.userInfoText;
    });
  }

  get lastOpenedWorkflows() {
    return this.lastOpened.pipe(
      map(transformations => {
        return transformations.filter(
          transformation => transformation.type === TransformationType.WORKFLOW
        );
      })
    );
  }

  get lastOpenedComponents() {
    return this.lastOpened.pipe(
      map(transformations => {
        return transformations.filter(
          transformation => transformation.type === TransformationType.COMPONENT
        );
      })
    );
  }

  select(selectedItem: Transformation) {
    this.tabItemService.addTransformationTab(selectedItem.id);
  }

  openTransformationContextMenu(
    selectedItem: Transformation,
    mouseEvent: MouseEvent
  ) {
    const { componentPortalRef } = this.contextMenuService.openContextMenu(
      new ComponentPortal(TransformationContextMenuComponent),
      {
        x: mouseEvent.clientX,
        y: mouseEvent.clientY
      }
    );

    componentPortalRef.instance.transformation = selectedItem;
  }

  newWorkflow(): void {
    this.transformationActionService.newWorkflow();
  }

  newComponent(): void {
    this.transformationActionService.newComponent();
  }
}
