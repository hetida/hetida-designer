import { Transformation } from './transformation';

export interface BaseItemDialogData {
  title: string;
  content: string;
  actionOk: string;
  actionCancel: string;
  deleteButtonText?: string;
  showDeleteButton?: boolean;
  transformation?: Transformation;
  disabledState: {
    name: boolean;
    category: boolean;
    tag: boolean;
    description: boolean;
  };
}
