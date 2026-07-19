import { HetidaSVGElement } from '../SVGTypes';

/**
 * Internal representation of a svg polygon element ands its properties
 */
export class HetidaSVGPolygon implements HetidaSVGElement {
  constructor(public elementConfig: Map<string, string>) {}
  readonly elementType: string = 'polygon';
  readonly subElements: HetidaSVGElement[] = [];
}
