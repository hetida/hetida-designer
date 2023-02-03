import { Connector } from './connector';

export interface Vertex {
  operator?: string;
  connector: Connector;
}
