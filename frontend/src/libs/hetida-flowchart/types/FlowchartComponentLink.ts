/**
 * Describes the information about a link between a input and output of two components
 */
export interface FlowchartComponentLink {
  uuid: string;
  from: string;
  to: string;
  path: number[][] | null;
  path_ids: string[] | null;
}

/**
 * checks if the given object fullfils the FlowchartComponentLink interface
 * @param object object to be checked
 */
export function isFlowchartComponentLink(
  object: any
): object is FlowchartComponentLink {
  const allAttributes = ['uuid', 'from', 'to', 'path', 'path_ids'].every(
    key => key in object
  );
  if (!allAttributes) {
    return false;
  }
  const types: { [key: string]: string[] } = {
    uuid: ['string'],
    from: ['string'],
    to: ['string']
  };
  const allTypes = Object.keys(types).every(key =>
    types[key].some(type => type === typeof object[key])
  );
  if (!allTypes) {
    return false;
  }
  if (typeof object.path_ids !== 'object') {
    return false;
  }
  if (
    object.path_ids !== null &&
    !object.path_ids.every((id: any) => typeof id === 'string')
  ) {
    return false;
  }
  if (typeof object.path !== 'object') {
    return false;
  }
  if (object.path !== null) {
    if (!Array.isArray(object.path_ids)) {
      return false;
    }
    if (object.path !== null && !Array.isArray(object.path)) {
      return false;
    }
    if (
      object.path !== null &&
      !object.path.every(
        (pair: any) =>
          Array.isArray(pair) && pair.every(value => typeof value === 'number')
      )
    ) {
      return false;
    }
    if (object.path.length !== object.path_ids.length) {
      return false;
    }
  } else {
    return object.path_ids === null;
  }
  return true;
}
