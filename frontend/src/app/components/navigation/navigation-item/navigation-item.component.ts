import { ComponentPortal } from '@angular/cdk/portal';
import { Component, Input, OnInit } from '@angular/core';
import { Observable } from 'rxjs';
import { first } from 'rxjs/operators';
import { navigationWidth } from 'src/app/constants/popoverSizes';
import { BaseItemType } from 'src/app/enums/base-item-type';
import { RevisionState } from 'src/app/enums/revision-state';
import { ComponentEditorService } from 'src/app/service/component-editor.service';
import { ContextmenuService } from 'src/app/service/contextmenu.service';
import { PopoverService } from 'src/app/service/popover.service';
import { WorkflowEditorService } from 'src/app/service/workflow-editor.service';
import { AbstractBaseItem, BaseItem } from '../../../model/base-item';
import { TabItemService } from '../../../service/tab-item/tab-item.service';
import { BaseItemContextMenuComponent } from '../../base-item-context-menu/base-item-context-menu.component';

@Component({
  selector: 'hd-navigation-item',
  templateUrl: './navigation-item.component.html',
  styleUrls: ['./navigation-item.component.scss']
})
export class NavigationItemComponent implements OnInit {
  @Input() abstractBaseItem: AbstractBaseItem;

  constructor(
    private readonly popoverService: PopoverService,
    private readonly contextmenuService: ContextmenuService,
    private readonly tabItemService: TabItemService,
    private readonly _workflowService: WorkflowEditorService,
    private readonly _componentService: ComponentEditorService
  ) {}

  /**
   * RevisionState
   */
  RevisionState = RevisionState;

  ngOnInit() {}

  public selectComponent(): void {
    this.popoverService.showPopover(
      this.abstractBaseItem.id,
      navigationWidth,
      null
    );
  }

  public closePopover(): void {
    this.popoverService.closePopover();
  }

  public editComponent(): void {
    this.tabItemService.addBaseItemTab(this.abstractBaseItem.id);
    this.popoverService.closePopover();
  }

  public dragComponent(event: DragEvent): void {
    event.dataTransfer.effectAllowed = 'all';
    event.dataTransfer.dropEffect = 'none';
    event.dataTransfer.setData(
      'hetida/baseItem',
      JSON.stringify(this.abstractBaseItem)
    );
  }

  public openContextMenu(mouseEvent: MouseEvent): void {
    const { componentPortalRef } = this.contextmenuService.openContextMenu(
      new ComponentPortal(BaseItemContextMenuComponent),
      {
        x: mouseEvent.clientX,
        y: mouseEvent.clientY
      }
    );

    let baseItem$: Observable<BaseItem>;

    if (this.abstractBaseItem.type === BaseItemType.COMPONENT) {
      baseItem$ = this._workflowService.getWorkflow(this.abstractBaseItem.id);
    } else if (this.abstractBaseItem.type === BaseItemType.WORKFLOW) {
      baseItem$ = this._componentService.getComponent(this.abstractBaseItem.id);
    } else {
      throw Error('type of abstract base item is invalid');
    }
    baseItem$
      .pipe(first())
      .subscribe(baseItem => (componentPortalRef.instance.baseItem = baseItem));
  }

  public get svgIcon(): string {
    if (this.abstractBaseItem.state === RevisionState.RELEASED) {
      return this.abstractBaseItem.type === BaseItemType.WORKFLOW
        ? 'icon-published-workflow'
        : 'icon-published-component';
    }
    return this.abstractBaseItem.type === BaseItemType.WORKFLOW
      ? 'icon-workflow'
      : 'icon-component';
  }
}
