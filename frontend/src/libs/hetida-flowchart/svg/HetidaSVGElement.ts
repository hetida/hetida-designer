/**
 * Internal representation of a svg element, its properties and its child elements
 */
export interface HetidaSVGElement {
  readonly elementConfig: Map<string, string>;
  readonly elementType: string;
  readonly subElements: HetidaSVGElement[];
}
