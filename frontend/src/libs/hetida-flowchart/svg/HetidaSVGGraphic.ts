import { HetidaSVGElement } from '../SVGTypes';
import { HetidaSVGElementConfigBuilder } from '../logic/HetidaSVGElementConfigBuilder';

/**
 * Internal representation of a svg graphics element, its properties and its child elements
 */
export class HetidaSVGGraphic implements HetidaSVGElement {
  constructor(
    public subElements: HetidaSVGElement[],
    nonInteractive: boolean = false
  ) {
    this.elementConfig = new HetidaSVGElementConfigBuilder()
      .setCustomAttribute('non-interactive', nonInteractive ? 'true' : 'false')
      .build();
  }
  readonly elementConfig: Map<string, string>;
  readonly elementType: string = 'g';
}
