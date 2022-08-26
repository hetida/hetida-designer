import {
  AdapterDataType,
  NodeSourceType,
  WiringDateRangeFilter
} from 'hd-wiring';

export interface InputWiring {
  workflow_input_name: string;
  adapter_id: string;
  ref_id?: string;
  ref_id_type?: NodeSourceType;
  ref_key?: string;
  type?: AdapterDataType;
  filters?: WiringDateRangeFilter | null | undefined;
}
