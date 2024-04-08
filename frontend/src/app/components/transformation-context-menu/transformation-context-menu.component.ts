import {
  AfterViewInit,
  ChangeDetectionStrategy,
  ChangeDetectorRef,
  Component,
  Input,
  OnDestroy,
  ViewChild
} from '@angular/core';
import { MatMenu, MatMenuTrigger } from '@angular/material/menu';
import { RevisionState } from 'src/app/enums/revision-state';
import { TransformationActionService } from 'src/app/service/transformation/transformation-action.service';
import { TabItemService } from '../../service/tab-item/tab-item.service';
import {
  isWorkflowTransformation,
  Transformation
} from '../../model/transformation';

@Component({
  selector: 'hd-transformation-context-menu',
  templateUrl: './transformation-context-menu.component.html',
  styleUrls: ['./transformation-context-menu.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush
})
export class TransformationContextMenuComponent
  implements AfterViewInit, OnDestroy
{
  @ViewChild(MatMenuTrigger) readonly _trigger: MatMenuTrigger;
  @ViewChild(MatMenu) readonly _menu: MatMenu;
  _isIncomplete: boolean;
  _isNotPublished: boolean;
  _isWorkflowWithoutIo: boolean;

  _transformation: Transformation;
  @Input()
  set transformation(transformation: Transformation) {
    // show or hide execute button
    this._isIncomplete =
      this.transformationActionService.isIncomplete(transformation);
    this._isNotPublished = transformation.state === RevisionState.DRAFT;
    // show or hide configureIO button in workflows
    this._isWorkflowWithoutIo =
      isWorkflowTransformation(transformation) &&
      this.transformationActionService.isWorkflowWithoutIo(transformation);
    this._transformation = transformation;
  }

  get transformation(): Transformation {
    return this._transformation;
  }

  constructor(
    public readonly changeDetector: ChangeDetectorRef,
    private readonly transformationActionService: TransformationActionService,
    private readonly tabItemService: TabItemService
  ) {}

  ngAfterViewInit(): void {
    this.changeDetector.detectChanges();
    this._menu.hasBackdrop = false;
    this._trigger.openMenu();
    this.changeDetector.detectChanges();
  }

  ngOnDestroy(): void {
    this._trigger.closeMenu();
  }

  openItem() {
    this.tabItemService.addTransformationTab(this.transformation.id);
  }

  editItem() {
    this.transformationActionService.editDetails(this.transformation);
  }

  openDocumentation() {
    this.transformationActionService.showDocumentation(
      this.transformation.id,
      false
    );
  }

  editDocumentation() {
    this.transformationActionService.showDocumentation(this.transformation.id);
  }

  copyItem() {
    this.transformationActionService.copy(this.transformation);
  }

  publish() {
    this.transformationActionService.publish(this.transformation);
  }

  delete() {
    this.transformationActionService.delete(this.transformation).subscribe();
  }

  async execute() {
    await this.transformationActionService.execute(this.transformation);
  }

  configureIO() {
    this.transformationActionService.configureIO(this.transformation);
  }

  deprecate() {
    this.transformationActionService.deprecate(this.transformation);
  }
}
