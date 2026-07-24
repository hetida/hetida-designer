import { FlowchartComponentIO } from '../Types';
import { isFlowchartComponentIO } from './FlowchartComponentIO';

/**
 * Describes a FlowchartComponent. Each component has a universally unique id, inputs and outputs
 */
export interface FlowchartComponent {
  uuid: string;
  name: string;
  revision: string;
  inputs: FlowchartComponentIO[];
  outputs: FlowchartComponentIO[];
  pos_x: number | null;
  pos_y: number | null;
  type: string;
  disabled: boolean;
}

/**
 * checks if the given object fullfils the FlowchartComponent interface
 * @param object object to be checked
 */
export function isFlowchartComponent(
  object: any
): object is FlowchartComponent {
  const allAttributes = [
    'uuid',
    'name',
    'revision',
    'inputs',
    'outputs',
    'pos_x',
    'pos_y',
    'type',
    'disabled'
  ].every(key => key in object);
  if (!allAttributes) {
    return false;
  }
  const types: { [key: string]: string[] } = {
    uuid: ['string'],
    name: ['string'],
    revision: ['string'],
    pos_x: ['number', 'object'],
    pos_y: ['number', 'object'],
    type: ['string'],
    disabled: ['boolean']
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
  if (!Array.isArray(object.inputs)) {
    return false;
  }
  if (!Array.isArray(object.outputs)) {
    return false;
  }
  if (!object.inputs.every((io: any) => isFlowchartComponentIO(io))) {
    return false;
  }
  if (!object.outputs.every((io: any) => isFlowchartComponentIO(io))) {
    return false;
  }
  if (typeof object.pos_x === 'object' && object.pos_x !== null) {
    return false;
  }
  if (typeof object.pos_y === 'object' && object.pos_y !== null) {
    return false;
  }

  return true;
}
