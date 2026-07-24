import { HetidaSVGElement } from '../SVGTypes';

/**
 * Internal representation of a svg rectangle element and its properties
 */
export class HetidaSVGRectangle implements HetidaSVGElement {
  constructor(public elementConfig: Map<string, string>) {}
  readonly elementType: string = 'rect';
  readonly subElements: HetidaSVGElement[] = [];
}
