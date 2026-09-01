import { IOType } from '../Types';

/**
 * Builder used to create SVG Element properties
 */
export class HetidaSVGElementConfigBuilder {
  constructor() {
    this.properties.set('x', 0);
    this.properties.set('y', 0);
  }
  public readonly properties = new Map<
    string,
    string | string[] | number | null
  >();
  public setWidth(width: number): HetidaSVGElementConfigBuilder {
    this.properties.set('width', width);
    return this;
  }
  public setHeight(height: number): HetidaSVGElementConfigBuilder {
    this.properties.set('height', height);
    return this;
  }
  public setPoints(points: [number, number][]): HetidaSVGElementConfigBuilder {
    const pointsString = points.map(pair => pair.join(','));
    this.properties.set('points', pointsString);
    return this;
  }
  public setClass(cssClass: string): HetidaSVGElementConfigBuilder {
    this.addCssClass(cssClass);
    return this;
  }
  public setId(id: string): HetidaSVGElementConfigBuilder {
    this.properties.set('id', id);
    return this;
  }
  public setLink(
    dataType: IOType,
    input: boolean,
    standalone: boolean
  ): HetidaSVGElementConfigBuilder {
    this.properties.set('dataType', dataType);
    if (!standalone) {
      this.addCssClass(input ? 'flowchart-input' : 'flowchart-output');
    }
    this.properties.set('canLink', 'true');
    this.properties.set('ioType', input ? 'input' : 'output');
    return this;
  }
  public setPosition(x: number, y: number): HetidaSVGElementConfigBuilder {
    this.properties.set('x', x);
    this.properties.set('y', y);
    return this;
  }
  public setEventDispatcher(
    dispatcher: boolean,
    type: string
  ): HetidaSVGElementConfigBuilder {
    if (dispatcher === true) {
      this.properties.set('dispatcher', type);
    }
    return this;
  }
  public setCenterPosition(
    x: number,
    y: number
  ): HetidaSVGElementConfigBuilder {
    this.properties.set('cx', x);
    this.properties.set('cy', y);
    return this;
  }
  public setRadius(radius: number): HetidaSVGElementConfigBuilder {
    this.properties.set('r', radius);
    return this;
  }
  public setCustomAttribute(
    name: string,
    value: string | string[] | number
  ): HetidaSVGElementConfigBuilder {
    this.properties.set(name, value);
    return this;
  }
  public build(): Map<string, string> {
    const map = new Map<string, string>();
    for (const property of this.properties) {
      if (property[1] === null) {
        continue;
      }
      if (Array.isArray(property[1])) {
        map.set(property[0], property[1].join(' '));
        continue;
      }
      map.set(property[0], String(property[1]));
    }
    return map;
  }
  private addCssClass(cssClass: string): void {
    const cssClasses = this.properties.get('class');
    if (cssClasses === null || cssClasses === undefined) {
      this.properties.set('class', [cssClass]);
    } else if (Array.isArray(cssClasses)) {
      cssClasses.push(cssClass);
    } else {
      throw new Error('Internal Error: invalid type for css classes');
    }
  }
}
