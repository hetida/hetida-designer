import { HetidaSVGElement } from '../SVGTypes';

export class HetidaSVGCircle implements HetidaSVGElement {
  constructor(public elementConfig: Map<string, string>) {}
  readonly elementType: string = 'circle';
  readonly subElements: HetidaSVGElement[] = [];
}
