import { RevisionState } from 'src/app/enums/revision-state';
import { BaseItemType } from 'src/app/enums/base-item-type';
import { WorkflowContent } from './workflow-content';
import { IoInterface } from './io-interface';
import { TestWiring } from './test-wiring';

// TODO move elsewhere?
export function isComponentTransformation(
  transformation: Transformation
): transformation is ComponentTransformation {
  return transformation.type === BaseItemType.COMPONENT;
}

export function isWorkflowTransformation(
  transformation: Transformation
): transformation is WorkflowTransformation {
  return transformation.type === BaseItemType.WORKFLOW;
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
