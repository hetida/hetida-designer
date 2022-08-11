import {
  AfterViewInit,
  ChangeDetectionStrategy,
  ChangeDetectorRef,
  Component,
  ElementRef,
  Input,
  OnDestroy,
  ViewChild
} from '@angular/core';
import { MatMenu, MatMenuTrigger } from '@angular/material/menu';
import { RevisionState } from 'src/app/enums/revision-state';
import { BaseItem } from 'src/app/model/base-item';
import { BaseItemActionService } from 'src/app/service/base-item/base-item-action.service';
import { TabItemService } from '../../service/tab-item/tab-item.service';
import { Transformation } from '../../model/new-api/transformation';

@Component({
  selector: 'hd-base-item-context-menu',
  templateUrl: './base-item-context-menu.component.html',
  styleUrls: ['./base-item-context-menu.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush
})
export class BaseItemContextMenuComponent implements AfterViewInit, OnDestroy {
  @ViewChild(MatMenuTrigger) readonly _trigger: MatMenuTrigger;
  @ViewChild(MatMenu) readonly _menu: MatMenu;
  @ViewChild('invisibleTrigger') _elementRef: ElementRef;
  _isIncomplete: boolean;
  _isNotPublished: boolean;
  baseItemHasEmptyInputsAndOutputs: boolean;

  _baseItem: BaseItem;
  @Input()
  set baseItem(baseItem: BaseItem) {
    // TODO
    this._isIncomplete = this.baseItemActionsService.isIncomplete(
      // @ts-ignore
      baseItem as Transformation
    );
    this._isNotPublished = baseItem.state === RevisionState.DRAFT;
    this.baseItemHasEmptyInputsAndOutputs =
      baseItem.inputs.length === 0 && baseItem.outputs.length === 0;
    this._baseItem = baseItem;
  }

  get baseItem(): BaseItem {
    return this._baseItem;
  }

  constructor(
    public readonly changeDetector: ChangeDetectorRef,
    private readonly baseItemActionsService: BaseItemActionService,
    private readonly tabItemService: TabItemService
  ) {}

  ngAfterViewInit(): void {
    this.changeDetector.detectChanges();
    this._menu.hasBackdrop = false;
    this._trigger.openMenu();
    (this._elementRef.nativeElement as HTMLButtonElement).focus();
    this.changeDetector.detectChanges();
  }

  ngOnDestroy(): void {
    this._trigger.closeMenu();
  }

  openItem() {
    this.tabItemService.addTransformationTab(this.baseItem.id);
  }

  editItem() {
    // @ts-ignore
    this.baseItemActionsService.editDetails(this.baseItem as Transformation);
  }

  openDocumentation() {
    this.baseItemActionsService.showDocumentation(this.baseItem.id, false);
  }

  editDocumentation() {
    this.baseItemActionsService.showDocumentation(this.baseItem.id);
  }

  async copyItem() {
    // TODO
    // @ts-ignore
    await this.baseItemActionsService.copy(this.baseItem as Transformation);
  }

  publish() {
    // TODO
    // @ts-ignore
    this.baseItemActionsService.publish(this.baseItem as Transformation);
  }

  delete() {
    this.baseItemActionsService
      // TODO
      // @ts-ignore
      .delete(this.baseItem as Transformation)
      .subscribe();
  }

  async execute() {
    await this.baseItemActionsService.execute(this.baseItem);
  }

  configureIO() {
    // TODO
    // @ts-ignore
    this.baseItemActionsService.configureIO(this.baseItem);
  }

  deprecate() {
    // TODO
    // @ts-ignore
    this.baseItemActionsService.deprecate(this.baseItem as Transformation);
  }
}
