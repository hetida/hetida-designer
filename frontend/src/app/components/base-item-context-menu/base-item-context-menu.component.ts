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
import {
  isWorkflowTransformation,
  Transformation
} from '../../model/new-api/transformation';

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
  _isWorkflowWithoutIo: boolean;

  _transformation: Transformation;
  @Input()
  set transformation(transformation: Transformation) {
    // show or hide execute button
    this._isIncomplete = this.baseItemActionsService.isIncomplete(
      transformation
    );
    this._isNotPublished = transformation.state === RevisionState.DRAFT;
    // show or hide configureIO button in workflows
    this._isWorkflowWithoutIo =
      isWorkflowTransformation(transformation) &&
      this.baseItemActionsService.isWorkflowWithoutIo(transformation);
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
    this.baseItemActionsService.copy(this.transformation);
  }

  publish() {
    this.baseItemActionsService.publish(this.transformation);
  }

  delete() {
    this.baseItemActionsService.delete(this.transformation).subscribe();
  }

  async execute() {
    await this.baseItemActionsService.execute(this.transformation);
  }

  configureIO() {
    this.baseItemActionsService.configureIO(this.transformation);
  }

  deprecate() {
    this.baseItemActionsService.deprecate(this.transformation);
  }
}
