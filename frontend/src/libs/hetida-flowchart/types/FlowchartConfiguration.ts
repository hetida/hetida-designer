import { FlowchartComponent, isFlowchartComponent } from './FlowchartComponent';
import {
  FlowchartComponentIO,
  isFlowchartComponentIO
} from './FlowchartComponentIO';
import {
  FlowchartComponentLink,
  isFlowchartComponentLink
} from './FlowchartComponentLink';

/**
 * Describes the information about an entire flowchart
 */
export interface FlowchartConfiguration {
  id: string;
  components: FlowchartComponent[];
  io: FlowchartComponentIO[];
  links: FlowchartComponentLink[];
}

/**
 * checks if the given object fullfils the FlowchartConfiguration interface
 * @param object object to be checked
 */
export function isFlowchartConfiguration(
  object: any
): object is FlowchartConfiguration {
  const allAttributes = ['components', 'io', 'links', 'id'].every(
    key => key in object
  );
  if (!allAttributes) {
    return false;
  }
  if (typeof object.id !== 'string') {
    return false;
  }
  if (!Array.isArray(object.components)) {
    return false;
  }
  if (!Array.isArray(object.io)) {
    return false;
  }
  if (!Array.isArray(object.links)) {
    return false;
  }
  if (
    !object.components.every((component: any) =>
      isFlowchartComponent(component)
    )
  ) {
    return false;
  }
  if (!object.io.every((io: any) => isFlowchartComponentIO(io))) {
    return false;
  }
  if (!object.links.every((link: any) => isFlowchartComponentLink(link))) {
    return false;
  }
  return true;
}
