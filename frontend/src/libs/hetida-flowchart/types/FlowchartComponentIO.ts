import { IOType } from './IOType';

/**
 * Describes the information about a input or output of a component
 */
export interface FlowchartComponentIO {
  uuid: string;
  data_type: IOType;
  name: string;
  input: boolean;
  pos_x: number | null;
  pos_y: number | null;
  constant: boolean;
  value: string;
  exposed?: boolean;
  is_default_value?: boolean;
}

/**
 * checks if the given object fullfils the FlowchartComponentIO interface
 * @param object object to be checked
 */
export function isFlowchartComponentIO(
  object: any
): object is FlowchartComponentIO {
  const allAttributes = [
    'uuid',
    'data_type',
    'name',
    'input',
    'pos_x',
    'pos_y',
    'constant',
    'value'
  ].every(key => key in object);
  if (!allAttributes) {
    return false;
  }
  const types: { [key: string]: string[] } = {
    uuid: ['string'],
    name: ['string'],
    data_type: ['string'],
    input: ['boolean'],
    pos_x: ['number', 'object'],
    pos_y: ['number', 'object'],
    constant: ['boolean'],
    value: ['string']
  };
  const allTypes = Object.keys(types).every(key =>
    types[key].some(type => type === typeof object[key])
  );
  if (!allTypes) {
    return false;
  }
  if (typeof object.pos_x !== typeof object.pos_y) {
    return false;
  }
  if (!Object.values(IOType).some(iotype => iotype === object.data_type)) {
    return false;
  }
  if (typeof object.pos_x === 'object' && object.pos_x !== null) {
    return false;
  }
  if (typeof object.pos_y === 'object' && object.pos_y !== null) {
    return false;
  }
  if (object.constant === true && object.value === '') {
    return false;
  }
  return true;
}
