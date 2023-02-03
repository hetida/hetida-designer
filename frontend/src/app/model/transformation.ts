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
  return transformation ? transformation.type === TransformationType.WORKFLOW : false;
}

export type Transformation = ComponentTransformation | WorkflowTransformation;

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
}
