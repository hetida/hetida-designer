import { InputWiring } from './input-wiring';
import { OutputWiring } from './output-wiring';

export interface TestWiring {
  // TODO move wiring interfaces to hd-wiring package
  input_wirings: InputWiring[];
  output_wirings: OutputWiring[];
}
