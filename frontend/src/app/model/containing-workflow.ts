import { RevisionState } from 'src/app/enums/revision-state';

/**
 * A workflow containing a transformation directly, i.e. as operator, and/or
 * nested, i.e. as operator of a workflow which is contained in it.
 */
export interface ContainingWorkflow {
  id: string;
  name: string;
  version_tag: string;
  state: RevisionState;
  /** Operators of this workflow which are instances of the transformation. */
  direct_operator_ids: string[];
  /** Workflows which are operators of this workflow and contain the transformation. */
  via_workflow_ids: string[];
}
