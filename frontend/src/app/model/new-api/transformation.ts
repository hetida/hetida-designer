import { RevisionState } from 'src/app/enums/revision-state';
import { BaseItemType } from 'src/app/enums/base-item-type';
import { WorkflowContent } from './workflow-content';
import { IoInterface, TestWiring } from 'hd-wiring';

// TODO move elsewhere?
export function isComponentTransformation(
  transformation: Transformation | null | undefined
): transformation is ComponentTransformation {
  return transformation
    ? transformation.type === BaseItemType.COMPONENT
    : false;
}

export function isWorkflowTransformation(
  transformation: Transformation | null | undefined
): transformation is WorkflowTransformation {
  return transformation ? transformation.type === BaseItemType.WORKFLOW : false;
}

export type Transformation = ComponentTransformation | WorkflowTransformation;

export interface ComponentTransformation extends AbstractTransformation {
  type: BaseItemType.COMPONENT;
  content: string;
}
export interface WorkflowTransformation extends AbstractTransformation {
  type: BaseItemType.WORKFLOW;
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
  type: BaseItemType;
  documentation?: string;
  content: string | WorkflowContent;
  io_interface: IoInterface;
  test_wiring: TestWiring;
}
