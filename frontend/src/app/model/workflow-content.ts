import { Constant } from './constant';
import { IOConnector } from './io-connector';
import { Link } from './link';
import { Operator } from './operator';

export interface WorkflowContent {
  operators: Operator[];
  links: Link[];
  inputs: IOConnector[];
  outputs: IOConnector[];
  constants: Constant[];
}
