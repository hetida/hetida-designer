import { HetidaSVGCircle } from '../svg/HetidaSVGCircle';
import {
  HetidaSVGElement,
  HetidaSVGForeignObject,
  HetidaSVGText
} from '../SVGTypes';
import {
  FlowchartComponentLink,
  PanDirections,
  SVGManipulatorConfiguration
} from '../Types';
import { HetidaSVGElementConfigBuilder } from './HetidaSVGElementConfigBuilder';
import {
  assert,
  checkForCycle,
  checkIfCoordinatesAreClose,
  convertCooordinatesToCommaSeperatedString,
  createLinkFromCoordinates,
  findAllLinksForIO,
  findParentElement,
  findPositionInCoordinates,
  getCoordinatesFromLink,
  getCoordinatesFromPolygon,
  getMidpointForPosition,
  isCloseTo,
  isOnLine,
  roundWithDecimals
} from './SVGHelper';
import { ThrotteledEventDispatcher } from './ThrotteledEventDispatcher';

/**
 * helper to allow indexing into an object that holds functions for relative position updates
 */
interface IndexableTransformFunctions {
  [key: string]: (
    element: SVGElement,
    value: string,
    relX: number,
    relY: number
  ) => void;
}

/**
 * helper to allow indexing into an object that holds functions for updating positions of different svg elements
 */
interface IndexablePositionFunctions {
  [key: string]: (x: number, y: number) => void;
}

/**
 * helper to allow indexing into an object that holds function for updating positions of different svg elements relative to a point
 */
interface IndexableRelativePositionFunctions {
  [key: string]: (element: Element, x: number, y: number) => void;
}

/**
 * helper to allow indexing into an object that holds panning information
 */
interface IndexablePanningData {
  [key: string]: [number, number];
}

/**
 * helper to structure the context menu entries with a label and their callback function
 * label and callback are not considered for 'hr' entries, but necessary for 'li' ones
 */
interface ContextMenuStructure {
  type: 'hr' | 'li';
  requiredInteraction: boolean;
  label?: string;
  callback?(event: MouseEvent): void;
}

/**
 * SVG Manipulator
 * bound to an svg element, this helper can
 * - create svg elements or groups thereof
 * - move svg elements or groups thereof
 * - remove svg elements or groups thereof
 * - create ghost links, which follow the mouse pointer
 * - create links between with either the input or output ioType attribute
 */
export class SVGManipulator {
  private readonly panningData: IndexablePanningData;

  /**
   * constructor which binds a svg element to this instance
   * @param svg svg element this manipulator instance knows of
   */
  constructor(
    public readonly svg: SVGSVGElement,
    public config: SVGManipulatorConfiguration = new SVGManipulatorConfiguration()
  ) {
    setTimeout(() => {
      const svgBox = this.svg.getBoundingClientRect();
      this.baseHeight = svgBox.height;
      this.baseWidth = svgBox.width;
    });
    // we listen to focus and blur, to register and remove the keydown event listener
    this.svg.setAttribute('tabindex', '-1');
    this.svg.setAttribute('dispatcher', 'svg');
    const keydownHandler = (event: KeyboardEvent) => this.keydownHandler(event);
    const keyupHandler = (event: KeyboardEvent) => this.keyupHandler(event);
    this.svg.addEventListener('focus', () => {
      document.addEventListener('keydown', keydownHandler);
      document.addEventListener('keyup', keyupHandler);
    });
    this.svg.addEventListener('blur', () => {
      document.removeEventListener('keydown', keydownHandler);
      document.removeEventListener('keyup', keyupHandler);
    });
    // we listen to resize events, to adjust the viewbox accordingly
    window.addEventListener('resize', () => this.resizeHandler());
    // we check every x ms if our internal size still matches the displayed size
    // TODO: replace with ResizeObserver when it becomes standardized
    setInterval(() => {
      this.resizeHandler();
    }, this.config.sizePollingTime);
    // we listen to wheel events for handling zooming
    this.svg.addEventListener('wheel', event => this.zoomHandler(event));
    // we listen to mouse move events on the svg for handling the
    // updating of the ghostlink, the dragging of elements and paning the viewBox, manipulation of links
    this.svg.addEventListener('mousemove', event =>
      this.mouseMoveHandler(event)
    );
    this.svg.addEventListener('mousedown', event =>
      this.mouseDownHandler(event)
    );
    this.svg.addEventListener('mouseup', event => this.mouseUpHandler(event));
    this.svg.parentElement?.addEventListener('mouseleave', event =>
      this.mouseUpHandler(event)
    );
    // we allow drag and drop interactions
    this.svg.addEventListener('dragover', event => {
      if (this.config.allowDrop) {
        event.preventDefault();
      }
    });
    // we anticipate a hetida component configuration as JSON string under the format 'hetida/component'
    this.svg.addEventListener('drop', event => this.dropHandler(event));
    // we have a custom contextmenu for components, links and the svg
    this.svg.addEventListener('contextmenu', event =>
      this.contextMenuHandler(event)
    );

    /**
     * helper that binds panning information to the attrivute name, for easy access
     */
    this.panningData = {
      north: [0, -this.config.panScale],
      south: [0, this.config.panScale],
      east: [-this.config.panScale, 0],
      west: [this.config.panScale, 0],
      northwest: [this.config.panScale, -this.config.panScale],
      northeast: [-this.config.panScale, -this.config.panScale],
      southwest: [this.config.panScale, this.config.panScale],
      southeast: [-this.config.panScale, this.config.panScale]
    };
  }

  private readonly svgNamespace = 'http://www.w3.org/2000/svg';
  // list of node names we allow to be deleted
  private readonly deletableNodes = [
    'rect',
    'text',
    'polygon',
    'line',
    'g',
    'path'
  ];
  private readonly eventDispatcher = new ThrotteledEventDispatcher(500);

  private scale = 1;
  private baseWidth = 0;
  private baseHeight = 0;
  private offsetX = 0;
  private offsetY = 0;

  // state management
  private ghostLink: Element | null = null;
  private linkFrom: HTMLElement | null = null;
  private activeLink: Element | null = null;
  private contextMenu: Element | null = null;
  private activeElement: Element | null = null;
  private dragElement: Element | null = null;
  private linkMarkerPosition: number | null = null;
  private readonly keysPressed = new Map<string, boolean>();

  /**
   * helper that binds the appropriate transformations functions to the attribute name, for easy access
   */
  private readonly positionTransformations: IndexableTransformFunctions = {
    x: this.transformX,
    y: this.transformY,
    points: this.transformPoints
  };

  /**
   * helper that binds the appropriate position update functions to the attribute name, for easy access
   */
  private readonly positionUpdates: IndexablePositionFunctions = {
    line: this.updatePositionForLine.bind(this),
    polygon: this.updatePositionForPolygon.bind(this),
    text: this.updatePositionForRectangleOrText.bind(this),
    rect: this.updatePositionForRectangleOrText.bind(this),
    g: this.updatePositionForGraphic.bind(this),
    circle: this.updatePositionForCircle.bind(this),
    path: () => {}
  };

  /**
   * helper that binds the appropriate relative position update functions to the attribute name, for easy access
   */
  private readonly relativePositionUpdates: IndexableRelativePositionFunctions =
    {
      text: this.updateRelativePositionForRectangleOrText.bind(this),
      rect: this.updateRelativePositionForRectangleOrText.bind(this),
      foreignObject: this.updateRelativePositionForRectangleOrText.bind(this),
      polygon: this.updateRelativePositionForPolygon.bind(this),
      g: this.updateRelativePositionForGraphic.bind(this)
    };

  /**
   * context menu definition for a component
   */
  private readonly componentMenu: ContextMenuStructure[] = [
    {
      type: 'li',
      label: 'Show Details',
      callback: () =>
        this.eventDispatcher.dispatchAsync(this.activeElement, 'select'),
      requiredInteraction: false
    },
    {
      type: 'hr',
      requiredInteraction: true
    },
    {
      type: 'li',
      label: 'Rename Operator',
      callback: () =>
        this.eventDispatcher.dispatchAsyncCustom(this.activeElement, 'rename'),
      requiredInteraction: true
    },
    {
      type: 'li',
      label: 'Remove',
      callback: () => this.destroyElement(this.activeElement),
      requiredInteraction: true
    },
    {
      type: 'hr',
      requiredInteraction: true
    },
    {
      type: 'li',
      label: 'Copy',
      callback: () =>
        this.eventDispatcher.dispatchAsyncCustom(this.activeElement, 'copy'),
      requiredInteraction: true
    },
    {
      type: 'li',
      label: 'Change Revision',
      callback: () =>
        this.eventDispatcher.dispatchAsyncCustom(
          this.activeElement,
          'revision'
        ),
      requiredInteraction: true
    }
  ];

  /**
   * context menu definition for a link
   */
  private readonly linkMenu: ContextMenuStructure[] = [
    {
      type: 'li',
      label: 'Delete Link',
      callback: () => this.destroyElement(this.activeElement),
      requiredInteraction: true
    }
  ];

  /**
   * context menu definition for a marker
   */
  private readonly markerMenu: ContextMenuStructure[] = [
    {
      type: 'li',
      label: 'Delete Marker',
      callback: () => this.removeLinkMarker(this.activeElement),
      requiredInteraction: true
    }
  ];

  /**
   * context menu definition for the svg
   */
  private readonly svgMenu: ContextMenuStructure[] = [
    {
      type: 'li',
      label: 'Show Details',
      callback: event =>
        this.eventDispatcher.dispatchAsyncCustom(this.svg, 'select', {
          x: event.clientX,
          y: event.clientY
        }),
      requiredInteraction: false
    },
    {
      type: 'hr',
      requiredInteraction: false
    },
    {
      type: 'li',
      label: 'Reset View',
      callback: () => this.showEntireWorkflow(),
      requiredInteraction: false
    }
  ];

  /**
   * helper to bind the context menu definitions to the node names
   */
  private readonly menusByNodeName: {
    [key: string]: { menu: ContextMenuStructure[]; cssClass?: string };
  } = {
    g: { menu: this.componentMenu, cssClass: 'component' },
    path: { menu: this.linkMenu },
    circle: { menu: this.markerMenu },
    svg: { menu: this.svgMenu }
  };

  /* PUBLIC API */

  /**
   * converts client x and y coordinates into the corresponding svg coordinates
   * @param clientX x coordinate of the client
   * @param clientY y coordinate of the client
   */
  public convertClientPositionIntoSVGPosition(
    clientX: number,
    clientY: number
  ): [number, number] {
    const ctm = this.svg.getScreenCTM();
    assert(ctm !== null, 'ScreenCTM not supported?');
    const xRaw = (clientX - ctm.e) * this.scale;
    const yRaw = (clientY - ctm.f) * this.scale;
    const x = roundWithDecimals(xRaw, 2);
    const y = roundWithDecimals(yRaw, 2);
    return [x, y];
  }

  /**
   * creats a element on the position of the event
   * @param element element to be created
   * @param posX relative x position inside the svg
   * @param posY relative y position inside the svg
   */
  public createElement(
    element: HetidaSVGElement,
    posX: number,
    posY: number
  ): void {
    assert(
      this.svg instanceof SVGSVGElement,
      'The svg element was not of type SVGSVGElement!'
    );
    const parent = this._createElement(element, posX, posY, this.svg);
    this.createChildElements(element, posX, posY, parent);
  }

  /**
   * creates a link between the two given elements
   * @param source element the link should start from
   * @param target element the link should end at
   */
  // eslint-disable-next-line complexity
  public createLink(
    source: Element,
    target: Element,
    config: FlowchartComponentLink | null = null
  ): void {
    const actualSource = this.getLinkConnector(source);
    const actualTarget = this.getLinkConnector(target);
    assert(
      actualSource.id !== '' && actualTarget.id !== '',
      'Neither source nor target id can be empty!'
    );
    const sourceDataType = actualSource.getAttribute('dataType');
    const targetDataType = actualTarget.getAttribute('dataType');
    assert(
      sourceDataType !== null && targetDataType !== null,
      'Missing datatype for link!'
    );
    // Datatypes must match, except if at least one is of type 'ANY'
    if (
      sourceDataType !== 'ANY' &&
      targetDataType !== 'ANY' &&
      sourceDataType !== targetDataType
    ) {
      return;
    }
    // if source and target belong to the same group, don't create a link
    const sourceParent = findParentElement(actualSource);
    const targetParent = findParentElement(actualTarget);
    if (sourceParent.isSameNode(targetParent)) {
      return;
    }
    // if we disallow cycles, check if we would create a cycle
    if (this.config.allowCyclicLinks === false) {
      if (this.checkForCyle(actualSource, actualTarget)) {
        return;
      }
    }
    // if there already is a link between these two elements, don't create a second one
    const sourceLinks = findAllLinksForIO(actualSource.id, this.svg);
    for (const sl of sourceLinks) {
      if (
        sl.getAttribute('link-start') === actualTarget.id ||
        sl.getAttribute('link-end') === actualTarget.id
      ) {
        return;
      }
    }
    // if the input already has a link, don't create a second one
    if (findAllLinksForIO(actualTarget.id, this.svg).length > 0) {
      return;
    }

    // if there a link to an input (output from workflow) don´t create link
    for (const sl of sourceLinks) {
      const linkEndId = sl.getAttribute('link-end');
      assert(linkEndId !== null, 'Missing link-end attribute for link!');

      const linkEndElement = this.svg.getElementById(linkEndId);
      const linkEndElementIsInput =
        linkEndElement.getAttribute('ioType') === 'input';

      const linkEndElementClass =
        linkEndElement.getAttribute('class') !== null
          ? linkEndElement.getAttribute('class')
          : '';

      // TODO add more information too an input (output from workflow).
      const linkEndElementIsFlowchartInput =
        linkEndElementClass.includes('flowchart-input');

      if (linkEndElementIsInput && !linkEndElementIsFlowchartInput) {
        return;
      }
    }

    const link = document.createElementNS(this.svgNamespace, 'path');
    if (config !== null) {
      link.id = config.uuid;
    }
    if (
      actualSource.getAttribute('non-interactive') === 'true' ||
      actualTarget.getAttribute('non-interactive') === 'true'
    ) {
      link.setAttribute('non-interactive', 'true');
    }
    link.setAttribute('class', `flowchart-link link-${sourceDataType}`);
    link.setAttribute('dataType', sourceDataType);
    let usedPath: string;
    if (config !== null && config.path !== null && config.path_ids !== null) {
      usedPath = createLinkFromCoordinates(config.path);
      link.setAttribute('custom-path', config.path_ids.join(','));
    } else {
      const startCoords = getCoordinatesFromPolygon(actualSource);
      const endCoords = getCoordinatesFromPolygon(actualTarget);
      if (this.config.linkOffsetSize === 0) {
        usedPath = `M${startCoords[1][0]} ${startCoords[1][1]} L ${
          endCoords[0][0] - 10
        } ${endCoords[1][1]}`;
      } else {
        usedPath = `M${startCoords[1][0]} ${startCoords[1][1]}
          L ${startCoords[1][0] + this.config.linkOffsetSize} ${
            startCoords[1][1]
          }
          L ${endCoords[0][0] - (this.config.linkOffsetSize + 10)} ${
            endCoords[1][1]
          }
          L ${endCoords[0][0] - 10} ${endCoords[1][1]}`;
        link.setAttribute('custom-path', 'x,x,x,x');
      }
    }
    link.setAttribute('d', usedPath);
    link.setAttribute('link-start', actualSource.id);
    link.setAttribute('link-end', actualTarget.id);
    link.setAttribute('dispatcher', 'link');
    this.renderToDOM(link, this.svg, true);
  }

  /**
   * zooms the viewBox of the svg element
   * @param zoomIn true for scaling the viewbox down (elements become larger), false for scaling the viewbox up (elements become smaller)
   */
  public zoomViewBox(
    zoomIn: boolean,
    zoomTo: [number, number] | null = null
  ): void {
    if (this.config.allowZooming === false) {
      return;
    }
    const newScale = Math.max(
      this.scale + this.config.zoomScale * (zoomIn ? -1 : 1),
      this.config.zoomScale
    );
    let zoomTargetX: number;
    let zoomTargetY: number;
    if (zoomTo !== null) {
      const clientRect = this.svg.getBoundingClientRect();
      zoomTargetX = zoomTo[0] - clientRect.left;
      zoomTargetY = zoomTo[1] - clientRect.top;
    } else {
      [zoomTargetX, zoomTargetY] = this.getCurrentCenter();
    }
    this._zoomViewbox(newScale, zoomTargetX, zoomTargetY);
  }

  /**
   * pans viewbox in given direction
   * @param direction given direction
   */
  public panViewBoxDirectional(direction: string): void {
    assert(
      Object.keys(this.panningData).some(key => key === direction),
      `Unknown direction '${direction}'`
    );
    this.panViewBox(...this.panningData[direction]);
  }

  /**
   * removes all elements from the svg, resets all internal state
   */
  public clearSVG(): void {
    const elementsToDelete = Array.from(this.svg.children).filter(
      child =>
        child.id !== this.config.backgroundElementId &&
        child.nodeName !== 'defs'
    );
    while (elementsToDelete.length > 0) {
      const child = elementsToDelete.pop();
      if (child === undefined) {
        continue;
      }
      child.remove();
    }
    this.activeElement = null;
    this.activeLink = null;
    this.contextMenu = null;
    this.ghostLink = null;
    this.linkFrom = null;
    this.dragElement = null;
    this.linkMarkerPosition = null;
  }

  /**
   * shows the entire workflow in the viewbox
   */
  public showEntireWorkflow(): void {
    // dont try and show the entrie workflow, if the svg is not visible
    if (this.svg.clientHeight === 0) {
      return;
    }

    const svgBox = this.svg.getBoundingClientRect();
    this.baseWidth = svgBox.width;
    this.baseHeight = svgBox.height;

    const components = Array.from(this.svg.getElementsByTagName('g'));
    if (components.length === 0) {
      return;
    }

    const parents = [
      ...new Set(components.map(component => findParentElement(component)))
    ] as SVGGElement[];

    parents.sort(
      (a, b) => Number(a.getAttribute('x')) - Number(b.getAttribute('x'))
    );
    const mostLeft = parents[0];
    const mostRight = parents[parents.length - 1];
    parents.sort(
      (a, b) => Number(a.getAttribute('y')) - Number(b.getAttribute('y'))
    );
    const mostTop = parents[0];
    const mostBottom = parents[parents.length - 1];

    const mostLeftBox = mostLeft.getBBox();
    const mostRightBox = mostRight.getBBox();
    const mostTopBox = mostTop.getBBox();
    const mostBottomBox = mostBottom.getBBox();

    const newOffsetX = mostLeftBox.x - this.config.showEntireWorkflowOffset;
    const newOffsetY = mostTopBox.y - this.config.showEntireWorkflowOffset;

    const targetWidth =
      mostRightBox.x +
      mostRightBox.width +
      this.config.showEntireWorkflowOffset -
      newOffsetX;
    const targetHeight =
      mostBottomBox.y +
      mostBottomBox.height +
      this.config.showEntireWorkflowOffset -
      newOffsetY;

    const scaleForWidth = targetWidth / this.baseWidth;
    const scaleForHeight = targetHeight / this.baseHeight;

    this.offsetX = newOffsetX;
    this.offsetY = newOffsetY;
    this.scale = Math.max(
      this.config.showEntrieWorkflowMinZoom,
      Math.max(scaleForWidth, scaleForHeight)
    );

    this.updateBackgroundElement();
    this.updateViewBox();
  }

  /**
   * lib.dom.d.ts makes SVGSVGElements return Element on getElementById instead of Element | null, this fixes this
   * @param id id of the element to find
   */
  public getElementFromSVGById(id: string): Element | null {
    return this.svg.getElementById(id);
  }

  /* Event Handling */

  /**
   * internal handler fpr wheel events
   * - handles zooming
   * @param event event used to determine the position the zoom should focus on
   */
  private zoomHandler(event: WheelEvent) {
    this.zoomViewBox(event.deltaY < 0, [event.x, event.y]);
    event.preventDefault();
  }

  /**
   * internal handler for keydown events
   * - registers key as pressed
   * - handles panning
   * @param event event used to determine what action to trigger
   */
  private keydownHandler(event: KeyboardEvent): void {
    this.keysPressed.set(event.key, true);
    for (const [key, pressed] of this.keysPressed.entries()) {
      if (pressed === false) {
        continue;
      }
      switch (key) {
        case 'ArrowUp':
          this.panViewBoxDirectional(PanDirections.NORTH);
          break;
        case 'ArrowLeft':
          this.panViewBoxDirectional(PanDirections.EAST);
          break;
        case 'ArrowDown':
          this.panViewBoxDirectional(PanDirections.SOUTH);
          break;
        case 'ArrowRight':
          this.panViewBoxDirectional(PanDirections.WEST);
          break;
        case this.config.cancelLinkingKey:
          this.cancelLinking(this.svg);
          break;
        default:
      }
    }
  }

  /**
   * internal handler for keyup events
   * - registers key as unpressed
   * @param event event used to determine the released key
   */
  private keyupHandler(event: KeyboardEvent): void {
    this.keysPressed.set(event.key, false);
  }

  /**
   * handles the mouse movement events
   * - ghost link follows the mouse cursor
   * - update position of element selected for dragging
   * @param event event to be handled
   */
  private mouseMoveHandler(event: MouseEvent): void {
    if (event.button !== 0) {
      return;
    }
    this.updateGhostLink(event);
    this.updatePosition(event);
  }

  /**
   * handles the mouse down events
   * - adding new link marker
   * - selecting link as active
   * - selecting source for ghost link
   * - selecting element for dragging
   * @param event event to be handled
   */
  private mouseDownHandler(event: MouseEvent): void {
    if (event.button !== 0) {
      return;
    }
    if (event.target === null) {
      return;
    }
    const target = event.target as HTMLElement;
    this.cancelLinking(target);
    this.addLinkMarker(target);
    this.selectActiveLink(target);
    this.selectLinkSource(target);
    this.showOptionalFields(target);
    this.selectElementForDragging(target);
  }

  /**
   * handles the mouse up events
   * - initalizes a link
   * - merges link markers
   * - deselectes element for dragging
   * @param event event to be handled
   */
  private mouseUpHandler(event: MouseEvent): void {
    this.closeContextMenu();
    if (event.button !== 0) {
      return;
    }
    this.initLink(event);
    this.snapElementToGrid();
    this.checkAndMergeLinkMarkers();
    this.stopDraggingElement();
  }

  /**
   * stops the drop event and let's a custom event bubble up with the coordinates in the svg and the original event attached
   * @param event event used to determine the position of the element
   */
  private dropHandler(event: DragEvent): void {
    event.stopPropagation();
    assert(
      event.dataTransfer !== null,
      'DropEvent without datatransfer is not expected!'
    );
    const json = event.dataTransfer.getData('hetida/transformation');
    const dropCoordinates = this.convertClientPositionIntoSVGPosition(
      event.x,
      event.y
    );
    // snap coordinates to grid
    const factor = this.config.gridSize > 0 ? this.config.gridSize : 1;
    const targetX = Math.round(dropCoordinates[0] / factor) * factor;
    const targetY = Math.round(dropCoordinates[1] / factor) * factor;
    this.eventDispatcher.dispatchAsyncCustom(this.svg, 'hetida-drop', {
      svgX: targetX,
      svgY: targetY,
      transformationJSON: json
    });
  }

  /**
   * handles showing the custom context menu
   * @param event event used to determine the position of the menu
   */
  private contextMenuHandler(event: MouseEvent): void {
    if (this.config.showContextMenu === false) {
      return;
    }
    if (event.target === null) {
      return;
    }
    const target = findParentElement(event.target as Element);
    if (
      Object.keys(this.menusByNodeName).every(key => key !== target.nodeName)
    ) {
      return;
    }
    if (
      target.nodeName === 'cirlce' &&
      target.classList.contains('link-marker-ghost')
    ) {
      return;
    }
    event.preventDefault();
    if (target.getAttribute('non-interactive') === 'true') {
      return;
    }
    const mousePosition: [number, number] = [event.pageX, event.pageY];

    if (target.nodeName === 'svg' && this.config.dispatchContextMenuEvent) {
      this.eventDispatcher.dispatchAsyncCustom(this.svg, 'customcontextmenu', {
        mousePosition
      });
      this.activeElement = target;
      return;
    }
    const menuStructure = this.menusByNodeName[target.nodeName];
    const isInteractive = !this.config.forceNonInteractiveContextMenu.some(
      key => key === target.nodeName
    );
    this.createContextMenu(mousePosition, menuStructure, isInteractive);
    this.activeElement = target;
  }

  /**
   * handles resizing the viewbox
   */
  private resizeHandler(): void {
    const svgBox = this.svg.getBoundingClientRect();
    if (this.baseWidth === svgBox.width && this.baseHeight === svgBox.height) {
      return;
    }
    this.baseWidth = svgBox.width;
    this.baseHeight = svgBox.height;
    this.updateViewBox();
  }

  /* Internal logic */

  private getCurrentWidth(): number {
    return this.baseWidth * this.scale;
  }
  private getCurrentHeight(): number {
    return this.baseHeight * this.scale;
  }
  private getCurrentCenter(): [number, number] {
    return [this.baseWidth / 2, this.baseHeight / 2];
  }

  /* DOM element manipulation */

  /**
   * Helper to create multiple levels of subelements
   * @param element the element with the subelements to be created
   * @param posX relative x position inside the svg
   * @param posY relative y position inside the svg
   * @param parent DOM parent element
   */
  private createChildElements(
    element: HetidaSVGElement,
    posX: number,
    posY: number,
    parent: SVGGraphicsElement
  ): void {
    for (const subElement of element.subElements) {
      const child = this._createElement(subElement, posX, posY, parent);
      this.createChildElements(subElement, posX, posY, child);
    }
  }

  /**
   * appends childElement to parentElement and dispatches the creation event
   * @param childElement child element to be appended
   * @param parentElement parent element being appended to
   */
  private renderToDOM(
    childElement: Element,
    parentElement: Element,
    prepend: boolean = false
  ): void {
    if (prepend) {
      // if we insert straight into the svg we need to mind the background element if there is one
      if (
        this.config.backgroundElementId !== null &&
        parentElement.isSameNode(this.svg)
      ) {
        const bg = this.getElementFromSVGById(this.config.backgroundElementId);
        assert(
          bg !== null,
          `The configured background element with the id '${this.config.backgroundElementId}' could not be found!`
        );
        bg.insertAdjacentElement('afterend', childElement);
      } else {
        parentElement.prepend(childElement);
      }
    } else {
      parentElement.appendChild(childElement);
    }
    this.eventDispatcher.dispatchAsync(childElement, 'create');
  }

  /**
   * dispatches the destruction event and removes the element from the dom
   * @param element element to be removed
   */
  private removeFromDOM(element: Element, silent: boolean): void {
    // needs to be synchronous, otherwise we delete the element before we dispatch the event
    if (!silent) {
      this.eventDispatcher.dispatch(element, 'destroy');
    }
    element.remove();
  }

  /**
   * adds the given properties to the given element
   * @param element element the properties should be added to
   * @param properties properties to be added
   * @param relX relative X coordinate
   * @param relY relative Y coordinate
   */
  private addProperties(
    element: SVGElement,
    properties: Map<string, string>,
    relX: number,
    relY: number
  ): void {
    for (const prop of properties) {
      // handle setting the position to be relative to the point of creation
      if (
        Object.keys(this.positionTransformations).some(pos => pos === prop[0])
      ) {
        this.positionTransformations[prop[0]](element, prop[1], relX, relY);
      } else {
        element.setAttribute(prop[0], prop[1]);
      }
    }
  }

  /**
   * handles the different creation methods of certain svg element types
   * @param element element to be created
   * @param relX relative x position inside the svg
   * @param relY relative y position inside the svg
   * @param parentElement parent element
   */
  private _createElement(
    element: HetidaSVGElement,
    relX: number,
    relY: number,
    parentElement: SVGGraphicsElement
  ): SVGGraphicsElement {
    if (element instanceof HetidaSVGText) {
      return this._createTextElement(element, relX, relY, parentElement);
    }
    if (element instanceof HetidaSVGForeignObject) {
      return this._createForeignElement(element, relX, relY, parentElement);
    }
    return this._createMiscElement(element, relX, relY, parentElement);
  }

  /**
   * handles the actual creation of any non specific svg element at the given position
   * and adding the created element inside the parent element
   * @param element element to be created
   * @param relX relative x position inside the svg
   * @param relY relative y position inside the svg
   * @param parentElement parent element
   */
  private _createMiscElement(
    element: HetidaSVGElement,
    relX: number,
    relY: number,
    parentElement: SVGGraphicsElement
  ): SVGGraphicsElement {
    const created = document.createElementNS(
      this.svgNamespace,
      element.elementType
    );
    // set attributes that are predefined by the configuration of the element
    this.addProperties(created, element.elementConfig, relX, relY);
    // add element to the parent element and fire create event
    assert(
      created instanceof SVGGraphicsElement,
      'We did not create a SVGGraphicsElement!'
    );
    this.renderToDOM(created, parentElement);
    return created;
  }

  /**
   * handles the actual creation of a foreignObject element at the given position and adding the text inside a p tag
   * @param element element to be created
   * @param relX relative x position inside the svg
   * @param relY relative y position inside the svg
   * @param parentElement parent element
   */
  private _createTextElement(
    element: HetidaSVGText,
    relX: number,
    relY: number,
    parentElement: SVGGraphicsElement
  ): SVGGraphicsElement {
    const created = document.createElementNS(
      this.svgNamespace,
      'foreignObject'
    );
    this.addProperties(created, element.elementConfig, relX, relY);
    const p = document.createElement('p');
    p.classList.add('text-overflow', 'text-unselectable');
    p.title = element.text;
    p.innerText = element.text;
    created.appendChild(p);
    this.renderToDOM(created, parentElement);
    return created;
  }

  /**
   * handles the actual creation of a foreignObject element at the given position and adding the custom html
   * @param element element to be created
   * @param relX relative x position inside the svg
   * @param relY relative y position inside the svg
   * @param parentElement parent element
   */
  private _createForeignElement(
    element: HetidaSVGForeignObject,
    relX: number,
    relY: number,
    parentElement: SVGGraphicsElement
  ): SVGGraphicsElement {
    const created = document.createElementNS(
      this.svgNamespace,
      'foreignObject'
    );
    this.addProperties(created, element.elementConfig, relX, relY);
    created.innerHTML = element.innerHTML;
    this.renderToDOM(created, parentElement);
    return created;
  }

  /**
   * removes a element from the DOM
   * @param element element to be removed
   */
  private destroyElement(element: Element | null, silent = false): boolean {
    if (element === null) {
      return false;
    }
    // we aren't allowed to delete this element, stop
    if (this.deletableNodes.every(name => name !== element.nodeName)) {
      return false;
    }
    // delete all child elements recursively
    for (const child of element.children) {
      this.destroyElement(child, silent);
    }
    const parent = element.parentElement;
    this._destroyElement(element, silent);
    if (parent === null) {
      return true;
    }
    this.destroyElement(parent, silent);
    this.activeElement = this.svg;
    if (!silent) {
      this.eventDispatcher.dispatchAsync(this.activeElement, 'select');
    }
    return true;
  }

  /**
   * handles the actual removal of the element, checks of links and removes them too
   * @param element element to be removed
   */
  private _destroyElement(element: Element, silent: boolean): void {
    const linkId = element.id;
    if (linkId !== '') {
      const links = findAllLinksForIO(linkId, this.svg);
      for (const link of links) {
        this._destroyElement(link, silent);
      }
      this.removeAllMarkersForLink(linkId);
    }
    this.removeFromDOM(element, silent);
  }

  /* Positioning */

  /**
   * handles the relative modification of the x coordinate of an element
   * @param element element to be modified
   * @param value current value of the x coordinate
   * @param relX relative change of the x coordinate
   */
  private transformX(
    element: SVGElement,
    value: string,
    relX: number,
    _: number
  ): void {
    element.setAttribute('x', (Number(value) + relX).toString());
  }

  /**
   * handles the relative modification of the y coordinate of an element
   * @param element element to be modified
   * @param value current value of the y coordinate
   * @param relY relative change of the y coordinate
   */
  private transformY(
    element: SVGElement,
    value: string,
    _: number,
    relY: number
  ): void {
    element.setAttribute('y', (Number(value) + relY).toString());
  }

  /**
   * handles the relative modification of the x and y coordinates of an element
   * @param element element to be modified
   * @param value current value of the describing points in the coordinate system
   * @param relX relative change of the x coordinate
   * @param relY relative change of the y coordinate
   */
  private transformPoints(
    element: SVGElement,
    value: string,
    relX: number,
    relY: number
  ) {
    const coords = value
      .split(' ')
      .map(pair => pair.split(',').map(strCoord => Number(strCoord)))
      .map(points => [points[0], points[1]] as [number, number]);
    for (const coord of coords) {
      coord[0] = coord[0] + relX;
      coord[1] = coord[1] + relY;
    }
    element.setAttribute(
      'points',
      convertCooordinatesToCommaSeperatedString(coords)
    );
  }

  /**
   * Updates the position of the given element to the position of the mouse
   * elements are dragged by their center points
   * @param mouseEvent event used to determine the position of the mouse
   */
  private updatePosition(mouseEvent: MouseEvent): void {
    const screenCTM = this.svg.getScreenCTM();

    // On IE getScreenCTM() is not supportted. We use a factor of 1 instead, to avoid a hard error.
    const transformFactorX = screenCTM?.a ?? 1;
    const transformFactorY = screenCTM?.d ?? 1;

    const x = mouseEvent.movementX / window.devicePixelRatio / transformFactorX;
    const y = mouseEvent.movementY / window.devicePixelRatio / transformFactorY;

    this._updatePosition(x, y);
  }

  /**
   * updates the position of the element selected for dragging
   * @param relX new x coordinate of elment
   * @param relY new y coordinate of element
   */
  private _updatePosition(relX: number, relY: number): void {
    if (this.dragElement === null) {
      return;
    }
    const nodeName = this.dragElement.nodeName;
    if (nodeName === 'svg') {
      this.panViewBox(-relX, -relY);
      return;
    }
    if (this.config.canMoveElements === false) {
      return;
    }
    assert(
      nodeName in this.positionUpdates,
      `Dragging a ${nodeName} is not (yet) supported!`
    );
    this.positionUpdates[nodeName](
      Math.round(relX * 2) / 2,
      Math.round(relY * 2) / 2
    );
    this.closeContextMenu();
    this.eventDispatcher.dispatchAsync(this.svg, 'select');
  }

  /**
   * Helper to update the position of a line element
   * @param x new x position
   * @param y new y position
   */
  private updatePositionForLine(x: number, y: number): void {
    if (this.dragElement === null) {
      return;
    }
    const oldX1 = Number(this.dragElement.getAttribute('x1'));
    const oldX2 = Number(this.dragElement.getAttribute('x2'));
    const oldY1 = Number(this.dragElement.getAttribute('y1'));
    const oldY2 = Number(this.dragElement.getAttribute('y2'));
    this.dragElement.setAttribute('x1', (oldX1 - x).toString());
    this.dragElement.setAttribute('x2', (oldX2 - x).toString());
    this.dragElement.setAttribute('y1', (oldY1 - y).toString());
    this.dragElement.setAttribute('y2', (oldY2 - y).toString());
  }

  /**
   * Helper to update the position of a polygon element
   * @param x new x position
   * @param y new y position
   */
  private updatePositionForPolygon(x: number, y: number): void {
    if (this.dragElement === null) {
      return;
    }
    assert(
      this.dragElement instanceof SVGPolygonElement,
      'Element was not of type SVGPolygonElement!'
    );
    const points = getCoordinatesFromPolygon(this.dragElement);
    for (const point of points) {
      point[0] = point[0] - x;
      point[1] = point[1] - y;
    }
    this.dragElement.setAttribute(
      'points',
      convertCooordinatesToCommaSeperatedString(points)
    );
  }

  /**
   * Helper to update the position of a rectangle or text element
   * @param x new x position
   * @param y new y position
   */
  private updatePositionForRectangleOrText(x: number, y: number): void {
    if (this.dragElement === null) {
      return;
    }
    const oldX = Number(this.dragElement.getAttribute('x'));
    const oldY = Number(this.dragElement.getAttribute('y'));
    this.dragElement.setAttribute('x', (oldX - x).toString());
    this.dragElement.setAttribute('y', (oldY - y).toString());
  }

  /**
   * Helper to update the position of a group of elements (g)
   * @param x new x position
   * @param y new y position
   */
  private updatePositionForGraphic(x: number, y: number): void {
    if (this.dragElement === null) {
      return;
    }
    assert(
      this.dragElement instanceof SVGGElement,
      'Element was not of type SVGGElement!'
    );
    const oldX = Number(this.dragElement.getAttribute('x'));
    const oldY = Number(this.dragElement.getAttribute('y'));
    this.dragElement.setAttribute('x', (oldX - x).toString());
    this.dragElement.setAttribute('y', (oldY - y).toString());
    for (const child of this.dragElement.children) {
      this.updatePositionRelative(child, x, y);
    }
  }

  /**
   * Helper to update the position of a circle element
   * @param x new x position
   * @param y new y position
   */
  private updatePositionForCircle(x: number, y: number): void {
    if (this.dragElement === null) {
      return;
    }
    const linkId = this.dragElement.getAttribute('link');
    assert(
      linkId !== null,
      'Dragging a circle not belonging to a link is not (yet) supported!'
    );
    const link = this.getElementFromSVGById(linkId);
    assert(link !== null, `No link for ID ${linkId} found!`);
    const elementX = Number(this.dragElement.getAttribute('cx'));
    const elementY = Number(this.dragElement.getAttribute('cy'));
    assert(
      this.linkMarkerPosition !== null,
      'Position within the link could not be determined!'
    );
    const linkPath = getCoordinatesFromLink(link);
    const newX = elementX + x;
    const newY = elementY + y;
    this.updateGhostMarkers(linkPath, [newX, newY]);
    this.dragElement.setAttribute('cx', newX.toString());
    this.dragElement.setAttribute('cy', newY.toString());
    linkPath[this.linkMarkerPosition] = [newX, newY];
    const updatedPath = createLinkFromCoordinates(linkPath);
    link.setAttribute('d', updatedPath);
  }

  /**
   * Helper to update the position in relation to a given points
   * @param element element whos position will be updated
   * @param relativeX relative change of the x coordinate
   * @param relativeY relative change of the y coordinate
   */
  private updatePositionRelative(
    element: Element,
    relativeX: number,
    relativeY: number
  ): void {
    assert(
      element.nodeName in this.relativePositionUpdates,
      `Moving a ${element.nodeName} relative to it's parent is not (yet) supported!`
    );
    this.relativePositionUpdates[element.nodeName](
      element,
      relativeX,
      relativeY
    );
  }

  /**
   * Helper to update the postion of a rectangle or text element in a relative way
   * @param element rectangle or text element
   * @param relX relative change of the x coordinate
   * @param relY relative change of the y coordinate
   */
  private updateRelativePositionForRectangleOrText(
    element: Element,
    relX: number,
    relY: number
  ): void {
    const oldX = Number(element.getAttribute('x'));
    const oldY = Number(element.getAttribute('y'));
    element.setAttribute('x', (oldX + relX).toString());
    element.setAttribute('y', (oldY + relY).toString());
  }

  /**
   * Helper to update the position of a polygon in a relative way
   * this updates the link between elements as well
   * @param element polygon element
   * @param relX relative change of the x coordinate
   * @param relY relative change of the y coordinate
   */
  private updateRelativePositionForPolygon(
    element: Element,
    relX: number,
    relY: number
  ): void {
    assert(
      element instanceof SVGPolygonElement,
      'Given element was not of type SVGPolygonElement!'
    );
    const points = getCoordinatesFromPolygon(element);
    for (const point of points) {
      point[0] = point[0] + relX;
      point[1] = point[1] + relY;
    }
    element.setAttribute(
      'points',
      convertCooordinatesToCommaSeperatedString(points)
    );
    // check if we could have a link, if we could, look for it and move it
    if (element.getAttribute('canLink') === 'true') {
      this.findAndUpdateLinkPosition(element);
    }
  }

  /**
   * Helper to update the position of a graphic in a relative way
   * this updates the child elements as well
   * @param element graphic element
   * @param relX relative change of the x coordinate
   * @param relY relative change of the y coordinate
   */
  private updateRelativePositionForGraphic(
    element: Element,
    relX: number,
    relY: number
  ): void {
    for (const child of element.children) {
      this.updatePositionRelative(child, relX, relY);
    }
    this.updateRelativePositionForRectangleOrText(element, relX, relY);
  }

  /**
   * keeps the defined backgroundelement in sync with the offsets
   */
  private updateBackgroundElement(): void {
    if (this.config.backgroundElementId === null) {
      return;
    }
    const bgElement = this.getElementFromSVGById(
      this.config.backgroundElementId
    );
    if (bgElement === null) {
      return;
    }
    assert(
      bgElement.nodeName === 'rect',
      `Updating a ${bgElement.nodeName} to be in sync with the offest is not (yet) supported!`
    );
    bgElement.setAttribute('x', this.offsetX.toString());
    bgElement.setAttribute('y', this.offsetY.toString());
  }

  /**
   * snaps the element selected for dragging to the grid
   */
  private snapElementToGrid(): void {
    if (this.dragElement === null) {
      return;
    }
    if (
      this.config.snapToGrid === false ||
      this.dragElement.nodeName === 'svg'
    ) {
      return;
    }
    assert(
      this.dragElement instanceof SVGGraphicsElement,
      'Given element was not of type SVGGraphicsElement!'
    );
    const bbox = this.dragElement.getBBox();
    const elementX = bbox.x - bbox.width / 2;
    let elementY: number;
    // if half of height is not even, adjust with the grid-size to make snapping clean
    if (bbox.height % 4 === 0) {
      elementY = bbox.y - bbox.height / 2;
    } else {
      elementY = bbox.y - (bbox.height + this.config.gridSize) / 2;
    }
    const factor = this.config.gridSize > 0 ? this.config.gridSize : 1;
    const targetX = Math.round(elementX / factor) * factor;
    const targetY = Math.round(elementY / factor) * factor;
    const moveX = targetX - elementX;
    const moveY = targetY - elementY;
    this._updatePosition(moveX, moveY);
  }

  /* Links */

  /**
   * creates a ghost link element, which is supposed to follow the mouse pointer
   * @param source element from which the ghost links starts
   */
  private createGhostLink(source: Element): Element {
    const target = this.getLinkConnector(source);
    // we take the second point as start of the link
    const startPoints = getCoordinatesFromPolygon(target);
    const dataType = target.getAttribute('dataType');
    assert(dataType !== null, 'start element for linking has no datatype!');
    const ghost = document.createElementNS(this.svgNamespace, 'path');
    ghost.setAttribute('class', `flowchart-ghost-link link-${dataType}`);
    if (target.getAttribute('ioType') === 'input') {
      if (this.config.linkOffsetSize === 0) {
        ghost.setAttribute(
          'd',
          `M${startPoints[0][0] - 10} ${startPoints[1][1]}`
        );
      } else {
        ghost.setAttribute(
          'd',
          `M${startPoints[0][0] - 10} ${startPoints[1][1]}
          L ${startPoints[0][0] - (this.config.linkOffsetSize + 10)} ${
            startPoints[1][1]
          }`
        );
      }
      ghost.setAttribute('source-input', '');
    } else if (target.getAttribute('ioType') === 'output') {
      if (this.config.linkOffsetSize === 0) {
        ghost.setAttribute('d', `M${startPoints[1][0]} ${startPoints[1][1]}`);
      } else {
        ghost.setAttribute(
          'd',
          `M${startPoints[1][0]} ${startPoints[1][1]}
          L ${startPoints[1][0] + this.config.linkOffsetSize} ${
            startPoints[1][1]
          }`
        );
      }
    }
    this.renderToDOM(ghost, this.svg, true);
    return ghost;
  }

  /**
   * updates the ghost link to follow the mouse pointer
   * @param ghost ghost link element
   * @param mouseEvent event used to determine the position of the mouse
   */
  private updateGhostLink(mouseEvent: MouseEvent): void {
    if (this.ghostLink === null) {
      return;
    }
    const [x, y] = this.convertClientPositionIntoSVGPosition(
      mouseEvent.clientX,
      mouseEvent.clientY
    );
    const lineValue = this.ghostLink.getAttribute('d');
    assert(lineValue !== null, 'the link is undefined!');
    const lineCoords = lineValue.split(' L '); // Format is 'M(x) (y) L (x) (y)'
    if (this.config.linkOffsetSize === 0) {
      if (lineCoords.length === 1) {
        lineCoords.push(` ${x} ${y}`);
      } else {
        lineCoords[1] = ` ${x} ${y}`;
      }
    } else {
      const isInput = this.ghostLink.getAttribute('source-input') !== null;
      if (lineCoords.length === 2) {
        if (isInput) {
          lineCoords.push(` ${x + this.config.linkOffsetSize} ${y}`);
        } else {
          lineCoords.push(` ${x - (this.config.linkOffsetSize + 10)} ${y}`);
        }
        lineCoords.push(` ${x} ${y}`);
      } else {
        if (isInput) {
          lineCoords[2] = ` ${x + this.config.linkOffsetSize} ${y}`;
        } else {
          lineCoords[2] = ` ${x - (this.config.linkOffsetSize + 10)} ${y}`;
        }
        lineCoords[3] = ` ${x} ${y}`;
      }
    }

    this.ghostLink.setAttribute('d', lineCoords.join(' L '));
  }

  /**
   * set target as active link
   * @param target target element
   */
  private selectActiveLink(target: Element): void {
    if (this.config.allowLinkModification === false) {
      return;
    }
    if (this.activeLink !== null && target.nodeName !== 'circle') {
      this.removeAllMarkersForLink(this.activeLink.id);
    }
    if (target.nodeName !== 'path') {
      return;
    }
    this.activeLink = target;
    const path = getCoordinatesFromLink(this.activeLink);
    this.createLinkMarkers(path);
  }

  /**
   * adds a new marker or updates the selected marker
   * @param mouseEvent event used to determine if and where a new marker should be placed
   * or if we are updating a existing one
   */
  private addLinkMarker(target: Element): void {
    if (this.activeLink === null) {
      return;
    }
    if (!(target instanceof SVGElement)) {
      return;
    }
    if (target.nodeName !== 'circle') {
      return;
    }
    if (!target.classList.contains('link-marker-ghost')) {
      return;
    }
    const x = Number(target.getAttribute('cx'));
    const y = Number(target.getAttribute('cy'));
    const coordinates = getCoordinatesFromLink(this.activeLink);
    if (this.findExisitingMarkerPosition(x, y, coordinates) !== null) {
      return;
    }
    const position = findPositionInCoordinates(x, y, coordinates);
    assert(
      position !== null,
      'Could not find a valid position for the marker element on the path!'
    );
    target.classList.remove('link-marker-ghost');
    target.classList.add('link-marker');
    const pathIds = this.activeLink.getAttribute('custom-path');
    let newIds: string[] = [];
    coordinates.splice(position, 0, [x, y]);
    if (pathIds === null) {
      // eslint-disable-next-line @typescript-eslint/no-unused-vars
      for (const _ of coordinates) {
        newIds.push('x');
      }
    } else {
      newIds = pathIds.split(',');
      newIds.splice(position, 0, 'x');
    }
    const lineValue = createLinkFromCoordinates(coordinates);
    this.activeLink.setAttribute('custom-path', newIds.join(','));
    this.activeLink.setAttribute('d', lineValue);

    const diffXPrev = coordinates[position][0] - coordinates[position - 1][0];
    const diffYPrev = coordinates[position][1] - coordinates[position - 1][1];
    const distancePrev = Math.hypot(diffXPrev, diffYPrev);
    if (
      distancePrev >
      this.config.markerRadius * this.config.minMarkerDistanceFactor
    ) {
      const ghostCoordsPrev: [number, number] = [
        (coordinates[position - 1][0] + coordinates[position][0]) / 2,
        (coordinates[position - 1][1] + coordinates[position][1]) / 2
      ];
      const ghostPrev = this._createLinkMarker(true, ...ghostCoordsPrev);
      if (ghostPrev !== null) {
        this.renderToDOM(ghostPrev, this.svg);
      }
    }
    const diffXNext = coordinates[position][0] - coordinates[position + 1][0];
    const diffYNext = coordinates[position][1] - coordinates[position + 1][1];
    const distanceNext = Math.hypot(diffXNext, diffYNext);
    if (
      distanceNext >
      this.config.markerRadius * this.config.minMarkerDistanceFactor
    ) {
      const ghostCoordsNext: [number, number] = [
        (coordinates[position][0] + coordinates[position + 1][0]) / 2,
        (coordinates[position][1] + coordinates[position + 1][1]) / 2
      ];
      const ghostNext = this._createLinkMarker(true, ...ghostCoordsNext);
      if (ghostNext !== null) {
        this.renderToDOM(ghostNext, this.svg);
      }
    }
  }

  /**
   * removes a link marker
   * @param element path element that the marker should be part of
   * @param mouseEvent event used to determine the position of the marker
   */
  private removeLinkMarker(element: Element | null): boolean {
    if (element === null) {
      return false;
    }
    if (element.nodeName !== 'circle') {
      return false;
    }
    if (element.classList.contains('link-marker-ghost')) {
      return false;
    }
    const linkId = element.getAttribute('link');
    assert(
      linkId !== null,
      'Dragging a circle not belonging to a link is not (yet) supported!'
    );
    const link = this.getElementFromSVGById(linkId);
    assert(link !== null, `No link for ID ${linkId} found!`);
    const x = Number(element.getAttribute('cx'));
    const y = Number(element.getAttribute('cy'));
    const coordinates = getCoordinatesFromLink(link);
    const position = this.findExisitingMarkerPosition(x, y, coordinates);
    assert(
      position !== null,
      'Position within the link could not be determined!'
    );
    const pathIds = link.getAttribute('custom-path');
    assert(pathIds !== null, 'no path ids');
    const markerIds = pathIds.split(',');

    const ghostCoordsPrev = getMidpointForPosition(position, coordinates);
    const ghostCoordsNext = getMidpointForPosition(position + 1, coordinates);

    const ghostsMarkers = Array.from(
      this.svg.getElementsByClassName('link-marker-ghost')
    );
    const ghostNext = ghostsMarkers.find(
      marker =>
        isCloseTo(Number(marker.getAttribute('cx')), ghostCoordsNext[0], 1) &&
        isCloseTo(Number(marker.getAttribute('cy')), ghostCoordsNext[1], 1)
    );
    const ghostPrev = ghostsMarkers.find(
      marker =>
        isCloseTo(Number(marker.getAttribute('cx')), ghostCoordsPrev[0], 1) &&
        isCloseTo(Number(marker.getAttribute('cy')), ghostCoordsPrev[1], 1)
    );
    if (ghostNext !== undefined) {
      ghostNext.remove();
    }
    if (ghostPrev !== undefined) {
      ghostPrev.remove();
    }

    markerIds.splice(position, 1);
    coordinates.splice(position, 1);
    link.setAttribute('d', createLinkFromCoordinates(coordinates));
    link.setAttribute('custom-path', markerIds.join(','));

    const newGhostCoords = getMidpointForPosition(position, coordinates);
    element.setAttribute('cx', newGhostCoords[0].toString());
    element.setAttribute('cy', newGhostCoords[1].toString());
    element.classList.remove('link-marker');
    element.classList.add('link-marker-ghost');
    this.eventDispatcher.dispatchAsync(link, 'drag');
    return true;
  }

  /**
   * finds position in the given coordinates that belongs to the given coordinates
   * @param x x coordinate of position
   * @param y y coordinate of position
   * @param coordinates coordinates the position is within
   */
  private findExisitingMarkerPosition(
    x: number,
    y: number,
    coordinates: [number, number][]
  ): number | null {
    const pos = coordinates.findIndex(c =>
      checkIfCoordinatesAreClose(c, [x, y], this.config.markerRadius)
    );
    return pos === -1 ? null : pos;
  }

  /**
   * creates the link markers to the given coordinates
   * @param coordiantes given coordinates
   */
  private createLinkMarkers(coordiantes: [number, number][]): void {
    const pointsBetween: [number, number][] = [];
    for (let i = 0; i < coordiantes.length - 1; i++) {
      const distance = Math.hypot(
        coordiantes[i][0] - coordiantes[i + 1][0],
        coordiantes[i][1] - coordiantes[i + 1][1]
      );
      if (
        distance <
        this.config.markerRadius * this.config.minMarkerDistanceFactor
      ) {
        continue;
      }

      const midX = (coordiantes[i][0] + coordiantes[i + 1][0]) / 2;
      const midY = (coordiantes[i][1] + coordiantes[i + 1][1]) / 2;
      pointsBetween.push([midX, midY]);
    }
    const markers = [];
    for (let i = 1; i < coordiantes.length - 1; i++) {
      const marker = this._createLinkMarker(false, ...coordiantes[i]);
      if (marker === null) {
        continue;
      }
      markers.push(marker);
    }
    for (const ghostCoords of pointsBetween) {
      const ghost = this._createLinkMarker(true, ...ghostCoords);
      if (ghost === null) {
        continue;
      }
      markers.push(ghost);
    }
    for (const marker of markers) {
      this.renderToDOM(marker, this.svg);
    }
  }

  /**
   * creates the actual link marker
   * @param ghost should the link marker be a ghost element
   * @param x x coordinate of the element
   * @param y y coordinate of the element
   */
  private _createLinkMarker(
    ghost: boolean,
    x: number,
    y: number
  ): SVGCircleElement | null {
    if (this.activeLink === null) {
      return null;
    }
    const dataType = this.activeLink.getAttribute('dataType');
    assert(dataType !== null, 'Link without datatype!');
    const circle = new HetidaSVGCircle(
      new HetidaSVGElementConfigBuilder()
        .setCenterPosition(x, y)
        .setRadius(this.config.markerRadius)
        .setClass('fill-white')
        .setClass(ghost ? 'link-marker-ghost' : 'link-marker')
        .setCustomAttribute('link', this.activeLink.id)
        .build()
    );

    const created = document.createElementNS(
      this.svgNamespace,
      circle.elementType
    );
    // set attributes that are predefined by the configuration of the element
    this.addProperties(created, circle.elementConfig, 0, 0);
    assert(created instanceof SVGCircleElement, 'did not create circle!');
    return created;
  }

  /**
   * removes all markers for the given link id
   * @param linkId given link id
   */
  private removeAllMarkersForLink(linkId: string): void {
    const circles = Array.from(this.svg.getElementsByTagName('circle')).filter(
      circle => circle.getAttribute('link') === linkId
    );
    while (circles.length > 0) {
      const removal = circles.pop();
      if (removal === undefined) {
        continue;
      }
      removal.remove();
    }
  }

  /**
   * find the ghostmarker beloging to the midpoints between the current link marker position and the offset position
   * @param linkPath coordinates of link markers
   * @param positionOffset 0 for previous, 1 for next position
   * @param ghostsMarkers all existing ghost markers
   */
  private findGhostMarker(
    linkPath: [number, number][],
    positionOffset: 0 | 1,
    ghostsMarkers: Element[]
  ): Element | undefined {
    if (this.linkMarkerPosition === null) {
      return undefined;
    }
    const ghostCoords: [number, number] = getMidpointForPosition(
      this.linkMarkerPosition + positionOffset,
      linkPath
    );
    const ghost = ghostsMarkers.find(marker => {
      const markerCoords: [number, number] = [
        Number(marker.getAttribute('cx')),
        Number(marker.getAttribute('cy'))
      ];
      return checkIfCoordinatesAreClose(markerCoords, ghostCoords, 1);
    });
    return ghost;
  }

  /**
   * update the position of a given ghost marker or recreate one, if necessary
   * @param linkPath coordinates of link markers
   * @param newCoordinates new coordinates of the changed link marker
   * @param positionOffset 1 for next, -1 for previous position
   * @param ghostMarker ghost marker to be updated or undefined if there is none
   */
  private updateGhostMarker(
    linkPath: [number, number][],
    newCoordinates: [number, number],
    positionOffset: 1 | -1,
    ghostMarker: Element | undefined
  ): void {
    if (this.linkMarkerPosition === null) {
      return;
    }
    const diffX =
      newCoordinates[0] - linkPath[this.linkMarkerPosition + positionOffset][0];
    const diffY =
      newCoordinates[1] - linkPath[this.linkMarkerPosition + positionOffset][1];
    const distance = Math.hypot(diffX, diffY);
    const updatedGhostCoords: [number, number] = [
      (newCoordinates[0] +
        linkPath[this.linkMarkerPosition + positionOffset][0]) /
        2,
      (newCoordinates[1] +
        linkPath[this.linkMarkerPosition + positionOffset][1]) /
        2
    ];
    if (ghostMarker === undefined) {
      if (
        distance >
        this.config.markerRadius * this.config.minMarkerDistanceFactor
      ) {
        const newGhostNext = this._createLinkMarker(
          true,
          ...updatedGhostCoords
        );
        assert(newGhostNext !== null, 'Could not recreate ghost link marker!');
        this.renderToDOM(newGhostNext, this.svg);
      }
      return;
    }

    if (
      distance <
      this.config.markerRadius * this.config.minMarkerDistanceFactor
    ) {
      ghostMarker.remove();
    } else {
      ghostMarker.setAttribute('cx', updatedGhostCoords[0].toString());
      ghostMarker.setAttribute('cy', updatedGhostCoords[1].toString());
    }
  }

  /**
   * Helper to update the position of ghost markers along the link path
   * @param linkPath path of the link
   * @param newCoordinates new coordinates of the changed link marker
   */
  private updateGhostMarkers(
    linkPath: [number, number][],
    newCoordinates: [number, number]
  ): void {
    if (this.linkMarkerPosition === null) {
      return;
    }
    const ghostsMarkers = Array.from(
      this.svg.getElementsByClassName('link-marker-ghost')
    );

    const ghostNext = this.findGhostMarker(linkPath, 1, ghostsMarkers);
    const ghostPrev = this.findGhostMarker(linkPath, 0, ghostsMarkers);

    this.updateGhostMarker(linkPath, newCoordinates, 1, ghostNext);
    this.updateGhostMarker(linkPath, newCoordinates, -1, ghostPrev);
  }

  /**
   * finds all links associated with the given element and updates their position to match up with the element
   * @param element element which has been moved
   */
  private findAndUpdateLinkPosition(element: Element): void {
    assert(
      element instanceof SVGPolygonElement,
      'Given element was not of type SVGPolygonElement!'
    );
    if (element.id === '') {
      return;
    }
    const links = findAllLinksForIO(element.id, this.svg);
    for (const link of links) {
      const d = link.getAttribute('d');
      assert(d !== null, 'Path is undefined!');
      const coordinates = getCoordinatesFromLink(link);
      const elementPos = getCoordinatesFromPolygon(element);
      if (element.getAttribute('ioType') === 'output') {
        this.findAndUpdateLinkPositionForOutput(coordinates, elementPos, link);
      } else if (element.getAttribute('ioType') === 'input') {
        this.findAndUpdateLinkPositionForInput(coordinates, elementPos, link);
      }
      const path = createLinkFromCoordinates(coordinates);
      link.setAttribute('d', path);
    }
  }

  /**
   * handles updating ghost markers and the link for outputs
   * @param coordinates coordinates of the link
   * @param elementPos coordinates of the polygon
   * @param link link element
   */
  private findAndUpdateLinkPositionForOutput(
    coordinates: [number, number][],
    elementPos: [number, number][],
    link: Element
  ): void {
    let marker;
    if (this.activeLink !== null) {
      // update the ghost marker
      marker = Array.from(
        this.svg.getElementsByClassName('link-marker-ghost')
      ).find(ghost => {
        const x = Number(ghost.getAttribute('cx'));
        const y = Number(ghost.getAttribute('cy'));
        return (
          x === (coordinates[0][0] + coordinates[1][0]) / 2 &&
          y === (coordinates[0][1] + coordinates[1][1]) / 2
        );
      });
    }
    coordinates[0] = [elementPos[1][0], elementPos[1][1]];
    // for untouched links, we update them with the offset part
    if (
      this.config.linkOffsetSize !== 0 &&
      link.getAttribute('custom-path') === null
    ) {
      coordinates[1] = [
        elementPos[1][0] + this.config.linkOffsetSize,
        elementPos[1][1]
      ];
    }
    if (marker !== undefined) {
      const markerX = (coordinates[0][0] + coordinates[1][0]) / 2;
      const markerY = (coordinates[0][1] + coordinates[1][1]) / 2;
      marker.setAttribute('cx', markerX.toString());
      marker.setAttribute('cy', markerY.toString());
    }
  }

  /**
   * handles updating ghost markers and the link for inputs
   * @param coordinates coordinates of the link
   * @param elementPos coordinates of the polygon
   * @param link link element
   */
  private findAndUpdateLinkPositionForInput(
    coordinates: [number, number][],
    elementPos: [number, number][],
    link: Element
  ): void {
    let marker;
    const lastPos = coordinates.length - 1;
    if (this.activeLink !== null) {
      // update the ghost marker
      marker = Array.from(
        this.svg.getElementsByClassName('link-marker-ghost')
      ).find(ghost => {
        const x = Number(ghost.getAttribute('cx'));
        const y = Number(ghost.getAttribute('cy'));
        return (
          x === (coordinates[lastPos][0] + coordinates[lastPos - 1][0]) / 2 &&
          y === (coordinates[lastPos][1] + coordinates[lastPos - 1][1]) / 2
        );
      });
    }
    coordinates[lastPos] = [elementPos[0][0] - 10, elementPos[1][1]];
    // for untouched links, we update them with the offset part
    if (
      this.config.linkOffsetSize !== 0 &&
      link.getAttribute('custom-path') === null
    ) {
      coordinates[lastPos - 1] = [
        elementPos[0][0] - (this.config.linkOffsetSize + 10),
        elementPos[1][1]
      ];
    }
    if (marker !== undefined) {
      const markerX =
        (coordinates[lastPos][0] + coordinates[lastPos - 1][0]) / 2;
      const markerY =
        (coordinates[lastPos][1] + coordinates[lastPos - 1][1]) / 2;
      marker.setAttribute('cx', markerX.toString());
      marker.setAttribute('cy', markerY.toString());
    }
  }

  /**
   * selects the input or output from which the ghost link will start
   * @param target element that is at the start of the ghost link
   */
  private selectLinkSource(target: HTMLElement): void {
    if (this.config.allowLinkCreation === false) {
      return;
    }
    if (this.linkFrom !== null) {
      return;
    }
    if (target.getAttribute('canLink') !== 'true') {
      return;
    }
    if (target.getAttribute('non-interactive') === 'true') {
      return;
    }
    this.linkFrom = target;
    this.ghostLink = this.createGhostLink(target);
  }

  private showOptionalFields(target: HTMLElement): void {
    const dispatcherAttrib = target.getAttribute('dispatcher');
    if (dispatcherAttrib) {
      this.eventDispatcher.dispatchAsyncCustom(target, dispatcherAttrib, {
        uuid: target.id
      });
    } else if (target.parentElement) {
      this.showOptionalFields(target.parentElement);
    }
  }

  /**
   * stops the link creation process
   */
  private cancelLinking(target: HTMLElement | SVGSVGElement): void {
    if (this.ghostLink === null) {
      return;
    }
    if (!target.isSameNode(this.svg)) {
      return;
    }
    this.destroyElement(this.ghostLink);
    this.ghostLink = null;
    this.linkFrom = null;
  }

  /**
   * creates a link between the source of the ghost link and the clicked element
   * @param event event used to determine the target element
   */
  private initLink(event: MouseEvent): void {
    if (this.linkFrom === null) {
      return;
    }
    if (this.ghostLink === null) {
      return;
    }
    if (event.target === null) {
      return;
    }
    const target = event.target as HTMLElement;
    // target validiation, needs to be either a output or input, the source needs to be the opposite
    if (target.getAttribute('canLink') !== 'true') {
      return;
    }
    const targetIoType = target.getAttribute('ioType');
    const linkFromIOType = this.linkFrom.getAttribute('ioType');
    if (targetIoType === null || linkFromIOType === null) {
      return;
    }
    if (targetIoType === linkFromIOType) {
      return;
    }
    if (target.getAttribute('non-interactive') === 'true') {
      return;
    }
    // if the source is a input element, we have to flip source and target
    if (linkFromIOType === 'input') {
      this.createLink(target, this.linkFrom);
    } else {
      this.createLink(this.linkFrom, target);
    }
    this.linkFrom = null;
    this.destroyElement(this.ghostLink);
    this.ghostLink = null;
  }

  /**
   * checks if two adjescent markers are close enough for merging, if yes merges them
   */
  private checkAndMergeLinkMarkers(): void {
    if (this.dragElement === null) {
      return;
    }
    if (this.linkMarkerPosition === null) {
      return;
    }
    if (!(this.dragElement instanceof SVGElement)) {
      return;
    }
    if (this.dragElement.nodeName !== 'circle') {
      return;
    }

    const linkId = this.dragElement.getAttribute('link');
    assert(linkId !== null, 'marker does not bleong to a link!');
    const link = this.getElementFromSVGById(linkId);
    assert(link !== null, `link with id ${linkId} could not be found!`);
    const linkCoords = getCoordinatesFromLink(link);

    const currentX = Number(this.dragElement.getAttribute('cx'));
    const currentY = Number(this.dragElement.getAttribute('cy'));

    const prevMarkerCoords = linkCoords[this.linkMarkerPosition - 1];
    const nextMarkerCoords = linkCoords[this.linkMarkerPosition + 1];

    if (
      checkIfCoordinatesAreClose(
        prevMarkerCoords,
        [currentX, currentY],
        this.config.markerRadius
      ) ||
      checkIfCoordinatesAreClose(
        nextMarkerCoords,
        [currentX, currentY],
        this.config.markerRadius
      ) ||
      isOnLine(prevMarkerCoords, nextMarkerCoords, [currentX, currentY])
    ) {
      this.removeLinkMarker(this.dragElement);
      this.dragElement = null;
    }
  }

  /**
   * gets the link connector to the given elements id
   * @param element given element
   */
  private getLinkConnector(element: Element): SVGPolygonElement {
    if (
      element instanceof SVGPolygonElement &&
      element.id.startsWith('link-')
    ) {
      return element;
    }
    const connector = this.getElementFromSVGById(`link-${element.id}`);
    assert(
      connector !== null && connector instanceof SVGPolygonElement,
      'Could not determine link source!'
    );
    return connector;
  }

  /* Viewbox Manipulation */

  /**
   * calculates all changes nessecary to show the viewbox at the newScale
   * @param newScale new scale the viewbox should be scaled to
   * @param zoomToX x coordinate of zoom reference point
   * @param zoomToY y coordinate of zoom reference point
   */
  private _zoomViewbox(
    newScale: number,
    zoomToX: number,
    zoomToY: number
  ): void {
    const oldScale = this.scale;
    const factor = newScale / oldScale;
    const x = zoomToX * oldScale + this.offsetX;
    const y = zoomToY * oldScale + this.offsetY;
    this.offsetX = (this.offsetX - x) * factor + x;
    this.offsetY = (this.offsetY - y) * factor + y;
    this.scale = newScale;
    this.updateBackgroundElement();
    this.updateViewBox();
  }

  /**
   * handles the panning of the viewBox in the four different directions
   * @param direction direction in which to pan the viewBox
   */
  private panViewBox(moveX: number, moveY: number): void {
    if (this.config.allowPanning === false) {
      return;
    }
    this.offsetX += moveX;
    this.offsetY += moveY;
    this.updateBackgroundElement();
    this.updateViewBox();
  }

  /**
   * helper to keep viewbox updates consistent
   */
  private updateViewBox(): void {
    if (isNaN(this.getCurrentHeight()) || isNaN(this.getCurrentWidth())) {
      return;
    }
    if (
      !isFinite(this.getCurrentHeight()) ||
      !isFinite(this.getCurrentWidth())
    ) {
      return;
    }
    this.svg.setAttribute(
      'viewBox',
      `${this.offsetX} ${
        this.offsetY
      } ${this.getCurrentWidth()} ${this.getCurrentHeight()}`
    );
  }

  /* Validation */

  /**
   * checks for cycles in the element graph starting from the given source element to the given target element
   * @param source element that is the end of the potential cycle
   * @param target element that is the start of the potential cycle
   */
  private checkForCyle(source: Element, target: Element): boolean {
    // check if source parent has inputs, if not there can't be a cycle
    const sourceParent = findParentElement(source);
    if (sourceParent.getElementsByClassName('flowchart-input').length === 0) {
      return false;
    }
    // check if tarhet parent has outputs, if not there can't be a cycle
    const targetParent = findParentElement(target);
    if (targetParent.getElementsByClassName('flowchart-output').length === 0) {
      return false;
    }
    // we could have created a cycle, so lets check if we can find a way from target to source along the existing links
    return checkForCycle(targetParent, source, this.svg);
  }

  /* Misc helpers */

  /**
   * selects the element that will be dragged
   * @param target element to be dragged
   */
  private selectElementForDragging(target: HTMLElement): void {
    if (this.ghostLink !== null) {
      return;
    }
    if (this.dragElement !== null) {
      return;
    }
    const pTarget = findParentElement(target);
    if (pTarget instanceof SVGPathElement) {
      return;
    }
    if (pTarget.getAttribute('non-drag') === 'true') {
      return;
    }
    this.activeElement = pTarget;
    this.dragElement = pTarget;
    if (pTarget instanceof SVGCircleElement) {
      this.selectLinkMarkerForDragging(pTarget);
    }
  }

  /**
   * handles the specialities of selecting a link marker element for dragging
   * @param target link marker element
   */
  private selectLinkMarkerForDragging(target: SVGCircleElement): void {
    const x = Number(target.getAttribute('cx'));
    const y = Number(target.getAttribute('cy'));
    const linkId = target.getAttribute('link');
    assert(linkId !== null, 'No Link belongs to this marker!');
    const link = this.getElementFromSVGById(linkId);
    assert(link !== null, `link width id ${linkId} could not be found!`);
    const coordiantes = getCoordinatesFromLink(link);
    this.linkMarkerPosition = this.findExisitingMarkerPosition(
      x,
      y,
      coordiantes
    );
  }

  /**
   * releases the currently selected drag element
   */
  private stopDraggingElement(): void {
    if (this.dragElement === null) {
      return;
    }
    this.eventDispatcher.dispatchAsync(this.dragElement, 'drag');
    const links = this.svg.getElementsByTagName('path');
    for (const link of links) {
      this.eventDispatcher.dispatchAsync(link, 'drag');
    }
    this.dragElement = null;
  }

  /* Context menu */

  /**
   * creates the given context menu at the given position
   * @param mousePosition given position
   * @param menuContent given context menu definition
   */
  private createContextMenu(
    mousePosition: [number, number],
    menuContent: { menu: ContextMenuStructure[]; cssClass?: string },
    isInteractive: boolean
  ): void {
    assert(this.contextMenu === null, 'A context menu is already open!');

    const menu = document.createElement('nav');
    const list = document.createElement('ul');
    menu.appendChild(list);

    for (const entry of menuContent.menu) {
      if (isInteractive === false && entry.requiredInteraction === true) {
        continue;
      }
      list.appendChild(this.createMenuElementFromEntry(entry));
    }
    if (list.children.length === 0) {
      return;
    }
    menu.classList.add('hetida-context-menu');
    this.svg.after(menu);

    const svgRect = this.svg.getBoundingClientRect();
    const menuRect = menu.getBoundingClientRect();
    // context menu would overflow right -> render left of mouse
    if (mousePosition[0] + menuRect.width > svgRect.right) {
      menu.style.left = `${
        mousePosition[0] - 2 - menu.clientWidth - svgRect.left
      }px`;
    } else {
      menu.style.left = `${mousePosition[0] + 2 - svgRect.left}px`;
    }
    // context menu would overflow bottom -> render above mouse
    if (mousePosition[1] + menuRect.height > svgRect.bottom) {
      menu.style.top = `${
        mousePosition[1] - 2 - menu.clientHeight - svgRect.top
      }px`;
    } else {
      menu.style.top = `${mousePosition[1] + 2 - svgRect.top}px`;
    }

    if (menuContent.cssClass !== undefined) {
      menu.classList.add(menuContent.cssClass);
    }

    this.contextMenu = menu;
  }

  /**
   * creates element corresponding to context menu structure
   * @param entry context menu entry or null for horizontal break line
   */
  private createMenuElementFromEntry(entry: ContextMenuStructure): Element {
    switch (entry.type) {
      case 'hr':
        return document.createElement('hr');
      case 'li':
        const element = document.createElement('li');
        assert(
          entry.label !== undefined && entry.callback !== undefined,
          'context menu element not fully configured!'
        );
        element.innerText = entry.label;
        element.addEventListener('mousedown', event => {
          assert(
            this.activeElement !== null,
            'no active element while context menu open!'
          );
          if (entry.callback !== undefined) {
            entry.callback(event);
          }
          this.closeContextMenu();
        });
        return element;
      default:
        throw new Error(`unknown context menu entry type ${entry.type}!`);
    }
  }

  /**
   * closes the context menu
   */
  private closeContextMenu(): void {
    // delete the reference.
    this.contextMenu = null;
    // workround for https://neusta-sd-west.atlassian.net/browse/GWHET-145
    // the function this.clearSVG() ereases in some cases the contextmenu reference (this.conextmenu)
    // before closeContextMenu can get in action.
    // clalling closeContextMenu() in this.clearSVG() function leads to wired behavior on creating the menu.
    // because of that, we find here all conext menus by selector and close them all.
    const contextMenues = document.getElementsByClassName(
      'hetida-context-menu'
    );
    for (const contextMenu of contextMenues) {
      contextMenu.remove();
    }
  }
}
