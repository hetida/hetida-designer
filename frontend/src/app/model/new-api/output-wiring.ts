import { RefIdType } from 'src/app/enums/ref-id-type';

export interface OutputWiring {
  workflow_output_name: string;
  adapter_id: number | string;
  ref_id?: string;
  ref_id_type?: RefIdType;
  ref_key?: string;
  type?: string;
}
