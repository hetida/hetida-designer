export interface IOItem {
  /**
   * UUID
   */
  id: string;

  /**
   * Data Type
   */
  type: string;

  /**
   * Name
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

  /**
   * operator id
   */
  operator?: string;

  /**
   * connector id
   */
  connector?: string;

  /**
   * is constant
   */
  constant?: boolean;

  /**
   * constant value
   */
  constantValue?: { value?: string };

  /**
   * Datasource or Datasink
   */
  // dataOriginId?: string;
}
