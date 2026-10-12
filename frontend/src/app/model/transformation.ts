import { RevisionState } from 'src/app/enums/revision-state';
import { TransformationType } from 'src/app/enums/transformation-type';
import { WorkflowContent } from './workflow-content';
import { IoInterface, TestWiring } from 'hd-wiring';

export function isComponentTransformation(
  transformation: Transformation | null | undefined
): transformation is ComponentTransformation {
  return transformation
    ? transformation.type === TransformationType.COMPONENT
    : false;
}

export function isWorkflowTransformation(
  transformation: Transformation | null | undefined
): transformation is WorkflowTransformation {
  return transformation
    ? transformation.type === TransformationType.WORKFLOW
    : false;
}

/**
 * The transformation store is populated with transformation stubs at startup:
 * They lack content, test_wiring, release_wiring and documentation, which can be
 * large (component code, manual input data) and are only needed when a
 * transformation is opened, executed, copied or modified. Use
 * TransformationService.ensureFullTransformation before accessing these fields
 * or before sending a transformation from the store to the backend.
 *
 * Full transformations from the backend always contain content and test_wiring,
 * while stubs never do.
 */
export function isFullTransformation(
  transformation: Transformation | null | undefined
): boolean {
  return (
    transformation !== null &&
    transformation !== undefined &&
    transformation.content !== undefined &&
    transformation.test_wiring !== undefined
  );
}

export type Transformation = ComponentTransformation | WorkflowTransformation;

export enum TrafoUpdateState {
  SUCCESS = 'SUCCESS',
  RESETTED_FROM_DB_BECAUSE_CHANGES_INTRODUCING_CYCLES_NOT_ALLOWED = 'RESETTED_FROM_DB_BECAUSE_CHANGES_INTRODUCING_CYCLES_NOT_ALLOWED',
  UNALLOWED_COMPONENT_IMPORTS = 'UNALLOWED_COMPONENT_IMPORTS'
}

export type UpdatedTransformation = Transformation & {
  update_state: TrafoUpdateState;
};

export interface ComponentTransformation extends AbstractTransformation {
  type: TransformationType.COMPONENT;
  content: string;
}
export interface WorkflowTransformation extends AbstractTransformation {
  type: TransformationType.WORKFLOW;
  content: WorkflowContent;
}

export interface AbstractTransformation {
  id: string;
  revision_group_id: string;
  name: string;
  description?: string;
  category: string;
  version_tag: string; // should be unique
  released_timestamp?: string;
  disabled_timestamp?: string;
  state: RevisionState;
  type: TransformationType;
  documentation?: string;
  content: string | WorkflowContent;
  io_interface: IoInterface;
  test_wiring: TestWiring;
  release_wiring?: TestWiring;
}

export interface UnitTestResults {
  pytest_stdout_str: string;
  pytest_stderr_str: string;
}
