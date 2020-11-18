import { Point } from './point';

export interface WorkflowLink {
  /**
   * UUID
   */
  id: string;

  /**
   * UUID of source operator
   */
  fromOperator: string;

  /**
   * UUID of source connector
   */
  fromConnector: string;

  /**
   * UUID of target operator
   */
  toOperator: string;

  /**
   * UUID of target connector
   */
  toConnector: string;

  /**
   * link path
   */
  path: Point[];
}
