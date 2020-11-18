import { BaseItemType } from 'src/app/enums/base-item-type';
import { BaseItem } from 'src/app/model/base-item';
import { ComponentBaseItem } from 'src/app/model/component-base-item';
import { WorkflowBaseItem } from 'src/app/model/workflow-base-item';

export function isComponentBaseItem(value: any): value is ComponentBaseItem {
  return (
    typeof value === 'object' &&
    value !== null &&
    'code' in value &&
    value.type === BaseItemType.COMPONENT
  );
}

export function isWorkflowBaseItem(value: any): value is WorkflowBaseItem {
  return (
    typeof value === 'object' &&
    value !== null &&
    'links' in value &&
    'operators' in value &&
    value.type === BaseItemType.WORKFLOW
  );
}

export function isBaseItem(value: any): value is BaseItem {
  return isComponentBaseItem(value) || isWorkflowBaseItem(value);
}
