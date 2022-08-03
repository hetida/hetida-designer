import { RevisionState } from 'src/app/enums/revision-state';
import { BaseItemType } from 'src/app/enums/base-item-type';
import { WorkflowContent } from './workflow-content';
import { IoInterface } from './io-interface';
import { TestWiring } from './test-wiring';

export interface Transformation {
  /**
   * Id of transformation (uuid)
   */
  id: string;

  /**
   * If transformation belongs to a group, this is the groupId (uuid)
   */
  revision_group_id: string;

  /**
   * Name of transformation
   */
  name: string;

  /**
   * Short description of transformation
   */
  description?: string;

  /**
   * Category of transformation
   */
  category: string;

  /**
   * Version tag of transformation (should be unique)
   */
  version_tag: string;

  /**
   * Transformation released (date-time)
   */
  released_timestamp?: string;

  /**
   * Transformation disabled (date-time)
   */
  disabled_timestamp?: string;

  /**
   * State of transformation (DRAFT, RELEASED, DISABLED)
   */
  state: RevisionState;

  /**
   * Type of transformation (COMPONENT or WORKFLOW)
   */
  type: BaseItemType;

  /**
   * Documentation of transformation
   */
  documentation?: string;

  /**
   * Content of transformation (string or WorkflowContent)
   */
  content: string | WorkflowContent;

  /**
   * I/O of transformation
   */
  io_interface: IoInterface;

  /**
   * Wiring of transformation
   */
  test_wiring: TestWiring;
}
