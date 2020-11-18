import { AbstractBaseItem } from './base-item';
import { BaseItemType } from '../enums/base-item-type';

export interface ComponentBaseItem extends AbstractBaseItem {
  type: BaseItemType.COMPONENT;

  /**
   * Code behind component
   */
  code: string;
}
