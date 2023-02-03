import { TransformationType } from 'src/app/enums/transformation-type';
import { RevisionState } from 'src/app/enums/revision-state';
import { Connector } from './connector';
import { Position } from './position';

export interface Operator {
  /**
   * Id of enclosed operator (uuid)
   */
  id: string;

  /**
   * If operator belongs to a group, this is the groupId (uuid)
   */
  revision_group_id: string;
  name: string;

  /**
   * Type of operator (COMPONENT or WORKFLOW)
   */
  type: TransformationType;

  /**
   * State of operator (DRAFT, RELEASED, DISABLED)
   */
  state: RevisionState;
  version_tag: string;
  transformation_id: string;
  inputs: Connector[];
  outputs: Connector[];
  position: Position;
}
