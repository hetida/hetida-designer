import { AbstractBaseItem } from './base-item';
import { WorkflowLink } from './workflow-link';
import { WorkflowOperator } from './workflow-operator';
import { BaseItemType } from '../enums/base-item-type';

export interface WorkflowBaseItem extends AbstractBaseItem {
  type: BaseItemType.WORKFLOW;

  /**
   * operators
   */
  operators: WorkflowOperator[];

  /**
   * links
   */
  links: WorkflowLink[];
}
