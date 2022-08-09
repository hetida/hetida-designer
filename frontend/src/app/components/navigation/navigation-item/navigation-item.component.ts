import { ComponentPortal } from '@angular/cdk/portal';
import { Component, Input } from '@angular/core';
import { Observable } from 'rxjs';
import { first } from 'rxjs/operators';
import { navigationWidth } from 'src/app/constants/popover-sizes';
import { BaseItemType } from 'src/app/enums/base-item-type';
import { RevisionState } from 'src/app/enums/revision-state';
import { ComponentEditorService } from 'src/app/service/component-editor.service';
import { ContextMenuService } from 'src/app/service/context-menu/context-menu.service';
import { PopoverService } from 'src/app/service/popover/popover.service';
import { WorkflowEditorService } from 'src/app/service/workflow-editor/workflow-editor.service';
import { BaseItem } from '../../../model/base-item';
import { TabItemService } from '../../../service/tab-item/tab-item.service';
import { BaseItemContextMenuComponent } from '../../base-item-context-menu/base-item-context-menu.component';
import { Transformation } from '../../../model/new-api/transformation';

@Component({
  selector: 'hd-navigation-item',
  templateUrl: './navigation-item.component.html',
  styleUrls: ['./navigation-item.component.scss']
})
export class NavigationItemComponent {
  @Input() transformation: Transformation;

  constructor(
    private readonly popoverService: PopoverService,
    private readonly contextMenuService: ContextMenuService,
    private readonly tabItemService: TabItemService,
    private readonly workflowEditorService: WorkflowEditorService,
    private readonly componentEditorService: ComponentEditorService
  ) {}

  /**
   * RevisionState
   */
  RevisionState = RevisionState;

  public selectComponent(): void {
    this.popoverService.showPopover(
      this.transformation.id,
      navigationWidth,
      null
    );
  }

  public editComponent(): void {
    this.tabItemService.addTransformationTab(this.transformation.id);
    this.popoverService.closePopover();
  }

  public dragComponent(event: DragEvent): void {
    // TODO check drag and drop
    event.dataTransfer.effectAllowed = 'all';
    event.dataTransfer.dropEffect = 'none';
    event.dataTransfer.setData(
      'hetida/baseItem',
      JSON.stringify(this.transformation)
    );
  }

  public openContextMenu(mouseEvent: MouseEvent): void {
    const { componentPortalRef } = this.contextMenuService.openContextMenu(
      new ComponentPortal(BaseItemContextMenuComponent),
      {
        x: mouseEvent.clientX,
        y: mouseEvent.clientY
      }
    );

    let baseItem$: Observable<BaseItem>;

    // TODO check base item given to context menu
    if (this.transformation.type === BaseItemType.WORKFLOW) {
      baseItem$ = this.workflowEditorService.getWorkflow(
        this.transformation.id
      );
    } else if (this.transformation.type === BaseItemType.COMPONENT) {
      baseItem$ = this.componentEditorService.getComponent(
        this.transformation.id
      );
    } else {
      throw Error('type of abstract base item is invalid');
    }
    baseItem$
      .pipe(first())
      .subscribe(baseItem => (componentPortalRef.instance.baseItem = baseItem));
  }

  public get svgIcon(): string {
    if (this.transformation.state === RevisionState.RELEASED) {
      return this.transformation.type === BaseItemType.WORKFLOW
        ? 'icon-published-workflow'
        : 'icon-published-component';
    }
    return this.transformation.type === BaseItemType.WORKFLOW
      ? 'icon-workflow'
      : 'icon-component';
  }
}
