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
