import { HetidaSVGElement } from '../SVGTypes';

/**
 * Internal representation of a svg text element and its properties
 * Creates a foreign object wrapping a paragraph (p) element
 */
export class HetidaSVGText implements HetidaSVGElement {
  constructor(
    public elementConfig: Map<string, string>,
    public readonly text: string
  ) {}
  readonly elementType: string = 'text';
  readonly subElements: HetidaSVGElement[] = [];
}
