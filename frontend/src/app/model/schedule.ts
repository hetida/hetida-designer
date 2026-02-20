import { TransformationState } from 'src/app/store/transformation/transformation.state';

export interface Schedule {
  id: string;
  active: boolean;
  name: string;
  transformation_id: string;
  transformation_name: string;
  transformation_version_tag: string;
  transformation_state: TransformationState;
  cron_expression: string;
  wiring: any;
  cron_expression_valid: boolean | null;
}
