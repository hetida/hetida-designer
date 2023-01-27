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

  _transformation: Transformation;
  @Input()
  set transformation(transformation: Transformation) {
    // TODO should configure io be enabled even if base item has empty inputs and outputs?
    this._isIncomplete = this.baseItemActionsService.isIncomplete(
      transformation
    );
    this._isNotPublished = transformation.state === RevisionState.DRAFT;
    // TODO is this the same as isIncomplete?
    // TODO if workflow, constants have to be empty, too
    this.baseItemHasEmptyInputsAndOutputs =
      transformation.io_interface.inputs.length === 0 &&
      transformation.io_interface.outputs.length === 0;
    this._transformation = transformation;
  }

  get transformation(): Transformation {
    return this._transformation;
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
    this.tabItemService.addTransformationTab(this.transformation.id);
  }

  editItem() {
    // TODO check for workflows
    this.baseItemActionsService.editDetails(this.transformation);
  }

  openDocumentation() {
    this.baseItemActionsService.showDocumentation(
      this.transformation.id,
      false
    );
  }

  editDocumentation() {
    this.baseItemActionsService.showDocumentation(this.transformation.id);
  }

  copyItem() {
    // TODO check for workflows
    this.baseItemActionsService.copy(this.transformation);
  }

  publish() {
    // TODO check for workflows
    this.baseItemActionsService.publish(this.transformation);
  }

  delete() {
    // TODO check for workflows
    this.baseItemActionsService.delete(this.transformation).subscribe();
  }

  async execute() {
    // TODO check for workflows
    await this.baseItemActionsService.execute(this.transformation);
  }

  configureIO() {
    // TODO check for workflows
    this.baseItemActionsService.configureIO(this.transformation);
  }

  deprecate() {
    // TODO check for workflows
    this.baseItemActionsService.deprecate(this.transformation);
  }
}
