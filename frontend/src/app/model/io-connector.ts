import { IOType } from 'hetida-flowchart';
import { Position } from './position';

export interface IOConnector {
  id: string;
  name: string | null;
  data_type: IOType;
  operator_id: string;
  connector_id: string;
  operator_name: string;
  connector_name: string;
  position: Position;
  value: string;
}
