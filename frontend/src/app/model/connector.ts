import { IOType } from 'hetida-flowchart';
import { Position } from './position';
import { IOTypeOption } from '../../../../../../hetida-flowchart/packages/hetida-flowchart/dist';

export interface Connector {
  id: string;
  name: string;
  data_type: IOType;
  position: Position;
  exposed?: boolean;
  type?: IOTypeOption;
  value?: string;
}
