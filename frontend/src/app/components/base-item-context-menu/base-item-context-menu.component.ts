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
  _isIncomplete$: Promise<boolean>;
  _isNotPublished: boolean;
  baseItemHasEmptyInputsAndOutputs: boolean;

  _baseItem: BaseItem;
  @Input()
  set baseItem(baseItem: BaseItem) {
    this._isIncomplete$ = this.baseItemActionsService.isIncomplete(baseItem);
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
    this.tabItemService.addBaseItemTab(this.baseItem.id);
  }

  editItem() {
    this.baseItemActionsService.editDetails(this.baseItem);
  }

  openDocumentation() {
    this.baseItemActionsService.showDocumentation(this.baseItem, false);
  }

  editDocumentation() {
    this.baseItemActionsService.showDocumentation(this.baseItem);
  }

  async copyItem() {
    await this.baseItemActionsService.copy(this.baseItem);
  }

  async publish() {
    await this.baseItemActionsService.publish(this.baseItem);
  }

  delete() {
    this.baseItemActionsService.delete(this.baseItem).subscribe();
  }

  async execute() {
    await this.baseItemActionsService.execute(this.baseItem);
  }

  configureIO() {
    this.baseItemActionsService.configureIO(this.baseItem);
  }

  showDocumentation() {
    this.baseItemActionsService.showDocumentation(this.baseItem);
  }

  deprecate() {
    this.baseItemActionsService.deprecate(this.baseItem);
  }
}
