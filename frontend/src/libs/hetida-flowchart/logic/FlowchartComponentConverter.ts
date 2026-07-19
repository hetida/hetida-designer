import {
  HetidaSVGForeignObject,
  HetidaSVGGraphic,
  HetidaSVGPolygon,
  HetidaSVGRectangle,
  HetidaSVGText
} from '../SVGTypes';
import {
  FlowchartComponent,
  FlowchartComponentIO,
  FlowchartComponentLink,
  FlowchartConfiguration,
  isFlowchartComponent,
  isFlowchartComponentIO,
  isFlowchartConfiguration
} from '../Types';
import { HetidaSVGElementConfigBuilder } from './HetidaSVGElementConfigBuilder';
import { assert } from './SVGHelper';
import { SVGManipulator } from './SVGManipulator';

export class FlowchartComponentConverter {
  // symbol represeting a workflow
  /* eslint-disable */
  // prettier-ignore
  private readonly workflowSVG = `<svg width='25' height='25' xmlns="http://www.w3.org/2000/svg" viewBox="0 0 500 300">
    <title>Workflow</title>
    <path d="M457.44,193.39V146.25H498V111.12H457.44V64H291.53v47.17H251v35.13h40.53v47.14H357v71H291.53v47.17H220.47V264.38H54.56v47.17H14v35.13H54.56v47.14H220.47V346.68h71.06v47.14H457.44V346.68H498V311.55H457.44V264.38H392v-71Zm-272.1,165.3H89.69V299.51h95.65Zm237-59.18v59.18H326.66V299.51ZM326.66,158.26V99.08H422.3v59.18Z"
      transform="translate(-14.03 -63.95)"/>
    </svg>`;
  /* eslint-enable */

  // symbol representing a component
  // prettier-ignore
  private readonly componentSVG = `<svg width='25' height='25' xmlns="http://www.w3.org/2000/svg" viewBox="0 0 500 300">
    <title>Component</title>
    <path d="M411.8,230.91V136.64H100.19v94.27h-81v50.23h81v94.22H411.8V281.14h81V230.91ZM361.57,214V325.14H150.41V186.86H361.57Z"
      transform="translate(-19.19 -136.64)"/>
    </svg>`;

  /**
   * Constant values for the layout of components, inputs and outputs
   */
  private readonly componentNameHeight = 50;
  private readonly componentWidth = 360;
  private readonly symbolSize = this.componentNameHeight / 2;
  private readonly spacing = 50;
  private readonly ioWidth = this.componentWidth / 2;
  private readonly ioHeight = 20;
  private readonly ioPadding = this.ioHeight / 2;
  private readonly ioOutSize = 20;

  /**
   * checks and renders the given flowchart configuration to the svg
   * @param configuration given flowchart configuration
   * @param manipulator svg manipulator
   * @param clearSVG should the svg be cleared before rendering the configuration
   */
  public loadFromConfiguration(
    configuration: FlowchartConfiguration,
    manipulator: SVGManipulator,
    clearSVG: boolean = false,
    initToEntireWorkflow: boolean = false
  ): void {
    assert(
      isFlowchartConfiguration(configuration),
      'Invalid flowchart configuration!'
    );

    // make sure all components have a x and y position
    assert(
      configuration.components.every(
        component => component.pos_x !== null && component.pos_y !== null
      ),
      'Loading a flowchart configuration requires defined positions for the components.'
    );

    // make sure all ios have a x and y position
    assert(
      configuration.io.every(io => io.pos_x !== null && io.pos_y !== null),
      'Loading a flowchart configuration requires defined positions of the workflow io.'
    );

    // make sure all links are valid
    for (const link of configuration.links) {
      // check links source to be either a component or io
      let source =
        configuration.components.findIndex(
          co =>
            co.outputs.findIndex(out => `link-${out.uuid}` === link.from) !== -1
        ) !== -1;
      source =
        source ||
        configuration.io.findIndex(io => `link-${io.uuid}` === link.from) !==
          -1;
      assert(
        source,
        'Loading a flowchart configuration requires all links to be valid!'
      );
      let target =
        configuration.components.findIndex(
          co =>
            co.inputs.findIndex(inp => `link-${inp.uuid}` === link.to) !== -1
        ) !== -1;
      target =
        target ||
        configuration.io.findIndex(io => `link-${io.uuid}` === link.to) !== -1;
      assert(
        target,
        'Loading a flowchart configuration requires all links to be valid!'
      );
    }

    if (clearSVG) {
      manipulator.clearSVG();
    }

    for (const component of configuration.components) {
      this.convertToSVGAtPosition(
        component,
        manipulator,
        component.pos_x,
        component.pos_y
      );
    }
    for (const io of configuration.io) {
      const hideLinkLabelForOptionalIO = configuration.links.some(
        link =>
          link.from.replace('link-', '') === io.uuid &&
          !manipulator.getElementFromSVGById(link.to)
      );
      if (!hideLinkLabelForOptionalIO) {
        // TODO: can we convince the compiler that we already checked for null above?

        this.convertToIO(io, manipulator, io.pos_x, io.pos_y);
      }
    }
    for (const link of configuration.links) {
      this.convertToLink(link, manipulator);
    }

    if (initToEntireWorkflow) {
      setTimeout(() => manipulator.showEntireWorkflow(), 150);
    }
  }

  /**
   * Converts the given FlowchartComponent into a SVG Element in the given svg DOM element at the position of the dragEvent
   * @param configuration FlowchartComponent to be drawn as SVG elements
   * @param manipulator Instance of the manipulator to create the SVG elements
   * @param dragEvent event used to determine the position of the new svg elements
   */
  public convertToSVG(
    configuration: FlowchartComponent | FlowchartComponentIO,
    manipulator: SVGManipulator,
    dragEvent: DragEvent
  ): void {
    const [x, y] = manipulator.convertClientPositionIntoSVGPosition(
      dragEvent.clientX,
      dragEvent.clientY
    );
    if (isFlowchartComponent(configuration)) {
      this.convertToSVGAtPosition(configuration, manipulator, x, y);
    } else if (isFlowchartComponentIO(configuration)) {
      this.convertToIO(configuration, manipulator, x, y);
    } else {
      throw new Error('unknown configuration!');
    }
  }

  /**
   * creates the io svg element from the configuration
   * @param ioConfig configuration of the io element
   * @param standalone if the io element is a standalone components (dispatches event) or not
   * @param x x coordinate of the io element
   * @param y y coordinate of the io element
   */
  private createIOElement(
    ioConfig: FlowchartComponentIO,
    standalone: boolean = false,
    x: number = 0,
    y: number = 0
  ): HetidaSVGGraphic {
    let rectanglePos: number[];
    let textPos: number[];
    let textWidth: number;
    let polygonPoints: [number, number][];

    if (standalone) {
      // x,y refer to the rectangle position
      rectanglePos = [x, y];
      let xOffset;
      if (ioConfig.input) {
        xOffset = this.ioOutSize;
        textPos = [x + this.ioOutSize + xOffset, y];
        textWidth = this.ioWidth - this.ioOutSize * 2;
      } else {
        xOffset = this.ioWidth - this.ioOutSize;
        textPos = [x - (this.ioWidth - this.ioOutSize * 1.5) + xOffset, y];
        textWidth = this.ioWidth - this.ioOutSize * 1.5;
      }
      polygonPoints = [
        [x + xOffset, y],
        [x + this.ioOutSize / 2 + xOffset, y + this.ioHeight / 2],
        [x + xOffset, y + this.ioHeight]
      ];
    } else {
      // x,y refer to the polygon position
      if (ioConfig.input) {
        rectanglePos = [x - this.ioOutSize, y];
        textPos = [x + this.ioOutSize, y];
        textWidth = this.ioWidth - this.ioOutSize * 2;
      } else {
        rectanglePos = [x - (this.ioWidth - this.ioOutSize), y];
        textPos = [x - (this.ioWidth - this.ioOutSize * 1.5), y];
        textWidth = this.ioWidth - this.ioOutSize * 1.5;
      }
      polygonPoints = [
        [x, y],
        [x + this.ioOutSize / 2, y + this.ioHeight / 2],
        [x, y + this.ioHeight]
      ];
    }

    const ioContainer = new HetidaSVGGraphic(
      [
        new HetidaSVGRectangle(
          new HetidaSVGElementConfigBuilder()
            .setWidth(ioConfig.constant ? this.ioWidth * 1.5 : this.ioWidth)
            .setHeight(this.ioHeight)
            .setClass(`type-${ioConfig.data_type}`)
            .setClass(ioConfig.is_default_value ? 'default-value-field' : '')
            .setPosition(
              ioConfig.constant
                ? rectanglePos[0] - this.ioWidth * 0.5
                : rectanglePos[0],
              rectanglePos[1]
            )
            .setId(ioConfig.uuid)
            .setEventDispatcher(standalone, 'io')
            .setLink(ioConfig.data_type, ioConfig.input, standalone)
            .setCustomAttribute(
              'non-interactive',
              standalone || ioConfig.constant ? 'true' : 'false'
            )
            .build()
        ),
        new HetidaSVGPolygon(
          new HetidaSVGElementConfigBuilder()
            .setLink(ioConfig.data_type, ioConfig.input, standalone)
            .setPoints(polygonPoints)
            .setId(`link-${ioConfig.uuid}`)
            .setClass('fill-white')
            .setCustomAttribute(
              'non-interactive',
              standalone || ioConfig.constant ? 'true' : 'false'
            )
            .build()
        ),
        new HetidaSVGText(
          new HetidaSVGElementConfigBuilder()
            .setPosition(textPos[0], textPos[1])
            .setHeight(this.ioHeight)
            .setWidth(textWidth)
            .setClass('text-white')
            .build(),
          ioConfig.name
        )
      ],
      standalone
    );
    if (ioConfig.constant === true) {
      ioContainer.subElements.push(
        new HetidaSVGText(
          new HetidaSVGElementConfigBuilder()
            .setPosition(
              textPos[0] - this.ioWidth * 0.5 - this.ioOutSize * 1.5,
              textPos[1]
            )
            .setHeight(this.ioHeight)
            .setWidth(textWidth * 0.75)
            .setClass('text-white')
            .build(),
          ioConfig.value
        )
      );
    }
    return ioContainer;
  }

  /**
   * creates the component svg element from the configuration
   * @param componentConfig configuration of the component
   */
  private createComponentElement(
    componentConfig: FlowchartComponent,
    hasOptionalFields: boolean = false
  ): HetidaSVGGraphic {
    const componentBodyHeight =
      Math.max(
        componentConfig.inputs.length -
          componentConfig.inputs.filter(
            input => input.is_default_value && !input.exposed
          ).length,
        componentConfig.outputs.length
      ) *
        (this.ioHeight + this.ioPadding) +
      this.ioPadding;

    const svgContainer = new HetidaSVGGraphic([
      new HetidaSVGRectangle(
        new HetidaSVGElementConfigBuilder()
          .setHeight(this.componentNameHeight + componentBodyHeight)
          .setWidth(this.componentWidth)
          .setClass('fill-darkgrey opacity-50')
          .setId(componentConfig.uuid)
          .setEventDispatcher(true, 'operator')
          .build()
      ),
      new HetidaSVGGraphic([
        new HetidaSVGRectangle(
          new HetidaSVGElementConfigBuilder()
            .setHeight(this.componentNameHeight)
            .setWidth(this.componentWidth)
            .setClass('fill-black')
            .build()
        ),
        new HetidaSVGForeignObject(
          new HetidaSVGElementConfigBuilder()
            .setWidth(this.symbolSize)
            .setHeight(this.symbolSize)
            .setPosition(this.symbolSize / 2, this.symbolSize / 2)
            .setClass(
              componentConfig.disabled ? 'state-disabled' : 'state-default'
            )
            .build(),
          componentConfig.type === 'COMPONENT'
            ? `${this.componentSVG}`
            : `${this.workflowSVG}`
        ),
        new HetidaSVGText(
          new HetidaSVGElementConfigBuilder()
            .setHeight(this.componentNameHeight / 2)
            .setWidth(this.componentWidth - 2 * this.spacing)
            .setPosition(this.spacing, 0)
            .setClass('text-white')
            .build(),
          componentConfig.name
        ),
        new HetidaSVGText(
          new HetidaSVGElementConfigBuilder()
            .setHeight(this.componentNameHeight / 2)
            .setWidth(this.componentWidth - 2 * this.spacing)
            .setPosition(this.spacing, this.componentNameHeight / 2)
            .setClass('text-yellow')
            .build(),
          `${componentConfig.revision}`
        )
      ])
    ]);

    if (hasOptionalFields) {
      svgContainer.subElements.push(
        new HetidaSVGGraphic([
          new HetidaSVGRectangle(
            new HetidaSVGElementConfigBuilder()
              .setPosition(0, this.componentNameHeight + componentBodyHeight)
              .setHeight(this.ioHeight)
              .setWidth(this.componentWidth)
              .setClass('fill-darkgray stroke-gray')
              .setId(componentConfig.uuid)
              .setEventDispatcher(true, 'showOptionalFields')
              .build()
          ),
          new HetidaSVGText(
            new HetidaSVGElementConfigBuilder()
              .setHeight(this.ioHeight)
              .setWidth(this.ioOutSize)
              .setPosition(
                this.ioWidth,
                this.componentNameHeight + componentBodyHeight
              )
              .setClass('text-white opacity-80 flowchart-input')
              .setEventDispatcher(true, 'showOptionalFields')
              .setId(componentConfig.uuid)
              .build(),
            '▼'
          )
        ])
      );
    }
    return svgContainer;
  }

  /**
   * Converts the given FlowchartComponent into a SVG Element in the given svg DOM element at the given position
   * @param component FlowchartComponent to be drawn as SVG elements
   * @param manipulator Instance of the manipulator to create the svg elements
   * @param posX position on the x axis
   * @param posY position on the y axis
   */
  public convertToSVGAtPosition(
    component: FlowchartComponent,
    manipulator: SVGManipulator,
    posX: number,
    posY: number
  ): void {
    const optionalInputs = component.inputs.filter(
      input => input.is_default_value
    ).length;

    // create rectangle for the full size of the component
    const element = this.createComponentElement(component, optionalInputs > 0);
    // create all inputs
    let x = 0;
    let y = this.componentNameHeight + this.ioPadding;

    for (const i of component.inputs) {
      let shouldAddInput = true;
      if (i.is_default_value && !i.exposed) {
        shouldAddInput = false;
      }
      if (shouldAddInput) {
        const subContainer = this.createIOElement(i, false, x, y);
        element.subElements.push(subContainer);
        y += this.ioHeight + this.ioPadding;
      }
    }
    // create all outputs
    x = this.componentWidth;
    y = this.componentNameHeight + this.ioPadding;
    for (const o of component.outputs) {
      const subContainer = this.createIOElement(o, false, x, y);
      element.subElements.push(subContainer);
      y += this.ioHeight + this.ioPadding;
    }
    // draw everything
    manipulator.createElement(element, posX, posY);
  }

  /**
   * convert a flowchart component link to a path between the svg elements with the from and to uuid
   * @param link link definition
   * @param manipulator instance of the svg manipulator bound to the svg
   */
  public convertToLink(
    link: FlowchartComponentLink,
    manipulator: SVGManipulator
  ): void {
    const linkFrom = manipulator.getElementFromSVGById(link.from);
    const linkTo = manipulator.getElementFromSVGById(link.to);
    if (linkFrom && linkTo) {
      manipulator.createLink(linkFrom, linkTo, link);
    }
  }

  /**
   * convert a io configuration into a svg element in the given svg DOM element at the given position
   * @param ioConfig IOConfiguration to be drawn as svg element
   * @param input is the io an input or output
   * @param manipulator Instance of the manipulator to create the svg elements
   * @param posX position on the x axis
   * @param posY position on the y axis
   */
  public convertToIO(
    ioConfig: FlowchartComponentIO,
    manipulator: SVGManipulator,
    posX: number,
    posY: number
  ): void {
    const ioElement = this.createIOElement(ioConfig, true);
    manipulator.createElement(ioElement, posX, posY);
  }
}
