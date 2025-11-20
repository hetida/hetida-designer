import { Component, DestroyRef, inject, Input, OnInit } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { Store } from '@ngrx/store';
import { NgHetidaFlowchartService } from 'ng-hetida-flowchart';
import { of, ReplaySubject, timer } from 'rxjs';
import { switchMap } from 'rxjs/operators';
import { TransformationType } from 'src/app/enums/transformation-type';
import { RevisionState } from 'src/app/enums/revision-state';
import { TransformationActionService } from 'src/app/service/transformation/transformation-action.service';
import { TransformationState } from 'src/app/store/transformation/transformation.state';
import {
  isWorkflowTransformation,
  Transformation
} from '../../model/transformation';
import { selectTransformationById } from '../../store/transformation/transformation.selectors';

@Component({
  selector: 'hd-toolbar',
  templateUrl: './toolbar.component.html',
  styleUrls: ['./toolbar.component.scss']
})
export class ToolbarComponent implements OnInit {
  public transformation: Transformation | undefined;
  public incompleteFlag = false;

  private readonly _transformationId$ = new ReplaySubject<string>();
  private readonly _destroyRef = inject(DestroyRef);

  @Input()
  set transformationId(transformationId: string) {
    this._transformationId$.next(transformationId);
  }

  constructor(
    private readonly transformationStore: Store<TransformationState>,
    private readonly flowchartService: NgHetidaFlowchartService,
    private readonly transformationActionService: TransformationActionService
  ) {}

  ngOnInit() {
    timer(0, 100)
      .pipe(
        takeUntilDestroyed(this._destroyRef),
        switchMap(() =>
          of(this.transformationActionService.isIncomplete(this.transformation))
        )
      )
      .subscribe(isIncomplete => {
        this.incompleteFlag = isIncomplete;
      });

    this._transformationId$
      .pipe(
        takeUntilDestroyed(this._destroyRef),
        switchMap(transformationId =>
          this.transformationStore.select(
            selectTransformationById(transformationId)
          )
        )
      )
      .subscribe(transformation => {
        this.transformation = transformation;
      });
  }

  zoomIn() {
    this.flowchartService.zoomIn(this.transformation.id);
  }

  zoomOut() {
    this.flowchartService.zoomOut(this.transformation.id);
  }

  showWorkflow() {
    this.flowchartService.showEntireWorkflow(this.transformation.id);
  }

  showDocumentation() {
    this.transformationActionService.showDocumentation(this.transformation.id);
  }

  async execute() {
    await this.transformationActionService.execute(this.transformation);
  }

  get isComponent(): boolean {
    return this.transformation.type === TransformationType.COMPONENT;
  }

  get isWorkflow(): boolean {
    return this.transformation.type === TransformationType.WORKFLOW;
  }

  get isWorkflowWithoutIo(): boolean {
    return (
      isWorkflowTransformation(this.transformation) &&
      this.transformationActionService.isWorkflowWithoutIo(this.transformation)
    );
  }

  get publishTooltip(): string {
    if (!this.isReleasedOrDeprecated()) {
      return 'Publish';
    }
    return 'Already published';
  }

  get upgradeWorkflowOperatorsTooltip(): string {
    if (!this.isReleasedOrDeprecated()) {
      return [
        'Upgrade workflow operators',
        // prettier-ignore
        '- DRAFT operators => update to revision\'s current state',
        '- RELEASED / DISABLED operators => newest revision in revision group'
      ].join('\n');
    }
    return 'Cannot upgrade operators for released workflows';
  }

  get updateExpandTooltip(): string {
    if (!this.isReleasedOrDeprecated()) {
      return 'Update and Expand code (Wirings, Formatting, Documentation)';
    }
    return 'Cannot change code for released component';
  }

  get unitTestTooltip(): string {
    return 'Run Unit Tests defined in Component Code';
  }

  publish(): void {
    this.transformationActionService.publish(this.transformation);
  }

  upgradeWorkflowOperators(): void {
    this.transformationActionService.upgradeWorkflowOperators(
      this.transformation
    );
  }

  updateExpand(): void {
    this.transformationActionService.updateExpand(this.transformation);
  }

  unitTestComponent(): void {
    this.transformationActionService.unitTestComponent(this.transformation);
  }

  configureIO() {
    this.transformationActionService.configureIO(this.transformation);
    this.incompleteFlag = this.transformationActionService.isIncomplete(
      this.transformation
    );
  }

  get deprecateTooltip(): string {
    if (!this.isReleased()) {
      return `Deprecate is disabled, because the ${this.transformation.type.toLowerCase()} is not released.`;
    }
    return 'Deprecate';
  }

  deprecate(): void {
    this.transformationActionService.deprecate(this.transformation);
  }

  copy() {
    this.transformationActionService.copy(this.transformation);
  }

  get newRevisionTooltip(): string {
    if (!this.isReleasedOrDeprecated()) {
      return `New revision is disabled, because the ${this.transformation.type.toLowerCase()} is not released.`;
    }
    return 'New revision';
  }

  newRevision() {
    this.transformationActionService.newRevision(this.transformation);
  }

  isReleased() {
    return this.transformation.state === RevisionState.RELEASED;
  }

  isDeprecated() {
    return this.transformation.state === RevisionState.DISABLED;
  }

  isReleasedOrDeprecated() {
    return (
      this.transformation.state === RevisionState.RELEASED ||
      this.transformation.state === RevisionState.DISABLED
    );
  }

  get executeTooltip(): string {
    if (this.incompleteFlag === true) {
      return `Cannot execute, because the ${this.transformation.type.toLowerCase()} is incomplete.`;
    }
    return 'Execute';
  }

  get deleteTooltip(): string {
    if (this.isReleasedOrDeprecated()) {
      return `Cannot delete this ${this.transformation.type.toLowerCase()}, because it is already released`;
    }
    return 'Delete';
  }

  delete() {
    this.transformationActionService.delete(this.transformation).subscribe();
  }

  editDetails(): void {
    this.transformationActionService.editDetails(this.transformation);
  }
}
