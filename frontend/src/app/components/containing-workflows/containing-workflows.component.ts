import { Component, Input, OnInit } from '@angular/core';
import { Store } from '@ngrx/store';
import { combineLatest } from 'rxjs';
import { first } from 'rxjs/operators';
import { RevisionState } from 'src/app/enums/revision-state';
import { ContainingWorkflow } from 'src/app/model/containing-workflow';
import { Transformation } from 'src/app/model/transformation';
import { TransformationHttpService } from 'src/app/service/http-service/transformation-http.service';
import { selectHashedTransformationLookupById } from 'src/app/store/transformation/transformation.selectors';
import { TransformationState } from 'src/app/store/transformation/transformation.state';

interface ContainingWorkflowRow {
  id: string;
  label: string;
  state: string;
  containedHow: string;
}

const stateLabels: Record<RevisionState, string> = {
  [RevisionState.DRAFT]: 'draft',
  [RevisionState.RELEASED]: 'released',
  [RevisionState.DISABLED]: 'deprecated'
};

const workflowLabel = (workflow: { name: string; version_tag: string }) =>
  `${workflow.name} (${workflow.version_tag})`;

/**
 * Lists the workflows containing a transformation, directly as operator or
 * nested in other workflows. Imports in component code are not considered.
 */
@Component({
  selector: 'hd-containing-workflows',
  templateUrl: './containing-workflows.component.html',
  styleUrls: ['./containing-workflows.component.scss'],
  standalone: false
})
export class ContainingWorkflowsComponent implements OnInit {
  @Input() transformationId: string;

  /** Undefined while loading */
  public _rows: ContainingWorkflowRow[] | undefined;
  public _loadingFailed = false;

  constructor(
    private readonly transformationHttpService: TransformationHttpService,
    private readonly transformationStore: Store<TransformationState>
  ) {}

  ngOnInit(): void {
    combineLatest([
      this.transformationHttpService.fetchContainingWorkflows(
        this.transformationId
      ),
      this.transformationStore
        .select(selectHashedTransformationLookupById)
        .pipe(first())
    ]).subscribe({
      next: ([containingWorkflows, transformationsById]) => {
        this._rows = this.toRows(containingWorkflows, transformationsById);
      },
      error: () => {
        this._loadingFailed = true;
      }
    });
  }

  private toRows(
    containingWorkflows: ContainingWorkflow[],
    transformationsById: Record<string, Transformation>
  ): ContainingWorkflowRow[] {
    const viaWorkflowLabel = (id: string): string => {
      // A nested workflow is contained in the list as well, unless it is a
      // DRAFT which no longer contains the transformation since the containing
      // workflow was stored.
      const workflow =
        containingWorkflows.find(candidate => candidate.id === id) ??
        transformationsById[id];
      return workflow === undefined ? id : workflowLabel(workflow);
    };

    return containingWorkflows.map(containingWorkflow => {
      const containedHow: string[] = [];
      const operatorCount = containingWorkflow.direct_operator_ids.length;
      if (operatorCount > 0) {
        containedHow.push(
          `directly as ${operatorCount} ${operatorCount === 1 ? 'operator' : 'operators'}`
        );
      }
      if (containingWorkflow.via_workflow_ids.length > 0) {
        containedHow.push(
          `indirectly via ${containingWorkflow.via_workflow_ids.map(viaWorkflowLabel).join(', ')}`
        );
      }

      return {
        id: containingWorkflow.id,
        label: workflowLabel(containingWorkflow),
        state: stateLabels[containingWorkflow.state],
        containedHow: containedHow.join(' and ')
      };
    });
  }
}
