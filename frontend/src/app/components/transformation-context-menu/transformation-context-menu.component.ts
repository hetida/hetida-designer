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
import { Subscription } from 'rxjs';
import { RevisionState } from 'src/app/enums/revision-state';
import { TransformationActionService } from 'src/app/service/transformation/transformation-action.service';
import { TransformationService } from 'src/app/service/transformation/transformation.service';
import { TabItemService } from '../../service/tab-item/tab-item.service';
import {
  isFullTransformation,
  isWorkflowTransformation,
  Transformation
} from '../../model/transformation';

@Component({
  selector: 'hd-transformation-context-menu',
  templateUrl: './transformation-context-menu.component.html',
  styleUrls: ['./transformation-context-menu.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush,
  standalone: false
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
  private fullTransformationSubscription: Subscription | undefined;

  @Input()
  set transformation(transformation: Transformation) {
    this._isNotPublished = transformation.state === RevisionState.DRAFT;
    this._transformation = transformation;
    this.fullTransformationSubscription?.unsubscribe();

    if (isFullTransformation(transformation)) {
      this.setContentDependentFlags(transformation);
      return;
    }

    // Stubs from the store lack the content these flags depend on. Hide the
    // respective entries until the full transformation is loaded.
    this._isIncomplete = true;
    this._isWorkflowWithoutIo = true;
    this.fullTransformationSubscription = this.transformationService
      .getFullTransformation(transformation.id)
      .subscribe(fullTransformation => {
        this._transformation = fullTransformation;
        this.setContentDependentFlags(fullTransformation);
        this.changeDetector.markForCheck();
      });
  }

  get transformation(): Transformation {
    return this._transformation;
  }

  constructor(
    public readonly changeDetector: ChangeDetectorRef,
    private readonly transformationActionService: TransformationActionService,
    private readonly transformationService: TransformationService,
    private readonly tabItemService: TabItemService
  ) {}

  ngAfterViewInit(): void {
    this.changeDetector.detectChanges();
    this._menu.hasBackdrop = false;
    this._trigger.openMenu();
    this.changeDetector.detectChanges();
  }

  ngOnDestroy(): void {
    this.fullTransformationSubscription?.unsubscribe();
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

  private setContentDependentFlags(transformation: Transformation): void {
    // show or hide execute button
    this._isIncomplete =
      this.transformationActionService.isIncomplete(transformation);
    // show or hide configureIO button in workflows
    this._isWorkflowWithoutIo =
      isWorkflowTransformation(transformation) &&
      this.transformationActionService.isWorkflowWithoutIo(transformation);
  }
}
