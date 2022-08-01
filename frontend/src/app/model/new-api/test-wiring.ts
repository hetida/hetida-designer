import { InputWiring } from './input-wiring';
import { OutputWiring } from './output-wiring';

export interface TestWiring {
  input_wirings: InputWiring[];
  output_wirings: OutputWiring[];
}
