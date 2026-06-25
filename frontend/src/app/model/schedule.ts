import { TestWiring } from 'hd-wiring';
import { TransformationType } from '../enums/transformation-type';
import { RevisionState } from '../enums/revision-state';

export interface Schedule {
  id: string;
  active: boolean;
  name: string;
  transformation_id: string | null;
  transformation_name: string | null;
  transformation_version_tag: string | null;
  transformation_state: RevisionState | null;
  transformation_type: TransformationType | null;
  cron_expression: string;
  wiring: TestWiring | null;
  cron_expression_valid: boolean | null;
}
