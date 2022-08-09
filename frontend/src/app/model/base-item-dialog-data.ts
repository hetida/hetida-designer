import { AbstractBaseItem } from './base-item';
import { Transformation } from './new-api/transformation';

export interface BaseItemDialogData {
  title: string;
  content: string;
  actionOk: string;
  actionCancel: string;
  deleteButtonText?: string;
  showDeleteButton?: boolean;
  // TODO remove
  abstractBaseItem: AbstractBaseItem;
  transformation?: Transformation;
  disabledState: {
    name: boolean;
    category: boolean;
    tag: boolean;
    description: boolean;
  };
}
