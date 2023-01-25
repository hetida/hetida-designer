import { Component, Input, OnInit } from '@angular/core';
import { Store } from '@ngrx/store';
import { NgHetidaFlowchartService } from 'ng-hetida-flowchart';
import { of, timer } from 'rxjs';
import { switchMap } from 'rxjs/operators';
import { BaseItemType } from 'src/app/enums/base-item-type';
import { RevisionState } from 'src/app/enums/revision-state';
import { BaseItemActionService } from 'src/app/service/base-item/base-item-action.service';
import { TransformationState } from 'src/app/store/transformation/transformation.state';
import {
  isWorkflowTransformation,
  Transformation
} from '../../model/new-api/transformation';
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
    private readonly baseItemAction: BaseItemActionService
  ) {}

  @Input() transformationId: string;

  transformation: Transformation | undefined;

  get isWorkflow(): boolean {
    return this.transformation.type === BaseItemType.WORKFLOW;
  }

  get isWorkflowWithoutIo(): boolean {
    return (
      isWorkflowTransformation(this.transformation) &&
      this.transformation.content.inputs.length === 0 &&
      this.transformation.content.outputs.length === 0 &&
      this.transformation.content.constants.length === 0
    );
  }

  incompleteFlag = false;

  ngOnInit() {
    timer(0, 100)
      .pipe(
        switchMap(() =>
          of(this.baseItemAction.isIncomplete(this.transformation))
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
    this.baseItemAction.showDocumentation(this.transformation.id);
  }

  async execute() {
    await this.baseItemAction.execute(this.transformation);
  }

  get publishTooltip(): string {
    if (!this.isReleased()) {
      return 'Publish';
    }
    return 'Already published';
  }

  // TODO check for workflows, depends on isWorkflowIncomplete
  publish(): void {
    this.baseItemAction.publish(this.transformation);
  }

  configureIO() {
    this.baseItemAction.configureIO(this.transformation);
    this.incompleteFlag = this.baseItemAction.isIncomplete(this.transformation);
  }

  get deprecateTooltip(): string {
    if (!this.isReleased()) {
      return `Deprecate is disabled, because the ${this.transformation.type.toLowerCase()} is not released.`;
    }
    return 'Deprecate';
  }

  deprecate(): void {
    this.baseItemAction.deprecate(this.transformation);
  }

  // TODO check for workflows
  copy() {
    this.baseItemAction.copy(this.transformation);
  }

  get newRevisionTooltip(): string {
    if (!this.isReleased()) {
      return `New revision is disabled, because the ${this.transformation.type.toLowerCase()} is not released.`;
    }
    return 'New revision';
  }

  // TODO check for workflows
  newRevision() {
    this.baseItemAction.newRevision(this.transformation);
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
    this.baseItemAction.delete(this.transformation).subscribe();
  }

  editDetails(): void {
    this.baseItemAction.editDetails(this.transformation);
  }
}
