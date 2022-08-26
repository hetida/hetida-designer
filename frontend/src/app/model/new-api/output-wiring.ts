import { AdapterDataType, NodeSourceType } from 'hd-wiring';

export interface OutputWiring {
  workflow_output_name: string;
  adapter_id: string;
  ref_id?: string;
  ref_id_type?: NodeSourceType;
  ref_key?: string;
  type?: AdapterDataType;
}
