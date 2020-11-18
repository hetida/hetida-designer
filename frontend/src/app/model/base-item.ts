import { BaseItemType } from '../enums/base-item-type';
import { RevisionState } from '../enums/revision-state';
import { Wiring } from '../service/http-service/wiring-http.service';
import { ComponentBaseItem } from './component-base-item';
import { IOItem } from './io-item';
import { WorkflowBaseItem } from './workflow-base-item';

export type BaseItem = ComponentBaseItem | WorkflowBaseItem;

export interface AbstractBaseItem {
  /**
   * Id of Item
   */
  id: string;

  /**
   * Type of Item (component or workflow)
   */
  type: BaseItemType;

  /**
   * If Item belongs to a group, this is the groupId
   */
  groupId: string;

  /*
   * Name of item
   */
  name: string;

  /**
   * Short description of item
   */
  description: string;

  /**
   * Category of item
   */
  category: string;

  /**
   * Version tag of item (should be unique)
   */
  tag: string;

  /**
   * State of Item (draft, released, disabled)
   */
  state: RevisionState;

  /**
   * Inputs of component / workflow
   */
  inputs: IOItem[];

  /**
   * Outputs of component / workflow
   */
  outputs: IOItem[];

  /**
   * wiring
   */
  wirings: Wiring[];
}
