import { Position } from './position';
import { Vertex } from './vertex';

export interface Link {
  id?: string;
  start: Vertex;
  end: Vertex;
  path?: Position[];
}
