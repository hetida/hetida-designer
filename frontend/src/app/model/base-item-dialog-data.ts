import { AbstractBaseItem } from './base-item';

export interface BaseItemDialogData {
  title: string;
  content: string;
  actionOk: string;
  actionCancel: string;
  deleteButtonText?: string;
  showDeleteButton?: boolean;
  abstractBaseItem: AbstractBaseItem;
  disabledState: {
    name: boolean;
    category: boolean;
    tag: boolean;
    description: boolean;
  };
}
