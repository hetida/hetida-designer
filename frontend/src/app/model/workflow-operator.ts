import { AbstractBaseItem } from './base-item';

export interface WorkflowOperator extends AbstractBaseItem {
  /**
   * UUID of enclosed item
   */
  itemId: string;

  /**
   * name of the operator
   */
  name: string;

  /**
   * y position
   */
  posY: number;

  /**
   * x position
   */
  posX: number;
}
