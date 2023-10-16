import { Component, Input, OnInit } from '@angular/core';
import { Store } from '@ngrx/store';
import { NgHetidaFlowchartService } from 'ng-hetida-flowchart';
import { of, timer } from 'rxjs';
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
  constructor(
    private readonly transformationStore: Store<TransformationState>,
    private readonly flowchartService: NgHetidaFlowchartService,
    private readonly transformationActionService: TransformationActionService
  ) {}

  @Input() transformationId: string;

  transformation: Transformation | undefined;

  get isWorkflow(): boolean {
    return this.transformation.type === TransformationType.WORKFLOW;
  }

  get isWorkflowWithoutIo(): boolean {
    return (
      isWorkflowTransformation(this.transformation) &&
      this.transformationActionService.isWorkflowWithoutIo(this.transformation)
    );
  }

  incompleteFlag = false;

  ngOnInit() {
    timer(0, 100)
      .pipe(
        switchMap(() =>
          of(this.transformationActionService.isIncomplete(this.transformation))
        )
      )
      .subscribe(isIncomplete => {
        this.incompleteFlag = isIncomplete;
      });
    this.transformationStore
      .select(selectTransformationById(this.transformationId))
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

  get publishTooltip(): string {
    if (!this.isReleased()) {
      return 'Publish';
    }
    return 'Already published';
  }

  publish(): void {
    this.transformationActionService.publish(this.transformation);
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
    if (!this.isReleased()) {
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

  get executeTooltip(): string {
    if (this.incompleteFlag === true) {
      return `Cannot execute, because the ${this.transformation.type.toLowerCase()} is incomplete.`;
    }
    return 'Execute';
  }

  get deleteTooltip(): string {
    if (this.isReleased()) {
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
