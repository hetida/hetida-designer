import { IOType, IOTypeOption } from 'hetida-flowchart';
import { Position } from './position';

export interface Connector {
  id: string;
  name: string;
  data_type: IOType;
  position: Position;
  exposed?: boolean;
  type?: IOTypeOption;
  value?: string;
}
