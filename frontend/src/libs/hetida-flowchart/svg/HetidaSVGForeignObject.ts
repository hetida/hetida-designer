import { HetidaSVGElement } from '../SVGTypes';

/**
 * Internal representation of a svg foreign object and its properties
 */
export class HetidaSVGForeignObject implements HetidaSVGElement {
  // TODO: innerHTML string might not be the best idea
  constructor(
    public elementConfig: Map<string, string>,
    public readonly innerHTML: string
  ) {}
  readonly elementType: string = 'foreignObject';
  readonly subElements: HetidaSVGElement[] = [];
}
