import { TestWiring } from 'hd-wiring';
import { TransformationType } from '../enums/transformation-type';
import { RevisionState } from '../enums/revision-state';

export interface Schedule {
  id: string;
  active: boolean;
  name: string;
  transformation_id: string;
  transformation_name: string;
  transformation_version_tag: string;
  transformation_state: RevisionState;
  transformation_type: TransformationType;
  cron_expression: string;
  wiring: TestWiring | null;
  cron_expression_valid: boolean | null;
}
