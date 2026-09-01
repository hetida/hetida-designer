/**
 * Describes the configuration options for the SVGManipulator
 */
export class SVGManipulatorConfiguration {
  // if false, the elements inside the svg will not be moved
  public canMoveElements = true;
  // if true, the links can form a cycle
  public allowCyclicLinks = false;
  // if true, allow panning of the workspace
  public allowPanning = true;
  // if true, allow zooming of the workspace
  public allowZooming = true;
  // zoom scale, default: 0.1
  public zoomScale = 0.1;
  // pan scale, default: 50
  public panScale = 50;
  // element to keep in sync with offsets (must be a rectangle!)
  public backgroundElementId: string | null = null;
  // key to cancel creating a link (default: 'Escape')
  public cancelLinkingKey = 'Escape';
  // raduis for the link markers (default: 5)
  public markerRadius = 5;
  // minimum distance between two markers (radius * x) to show ghost markers
  public minMarkerDistanceFactor = 4;
  // x-axis offset for a link, 0 disabled this feature (default: 25)
  // the offsets are treated link normal link marker points
  public linkOffsetSize = 0;
  // if true, the elements will snap to a grid aligned position after dragging finished
  public snapToGrid = true;
  public gridSize = 5;
  // set default zoom level (default: 1)
  public defaultZoom = 1;
  // if true, the custom context menu will show, otherwise the default
  public showContextMenu = true;
  // if true, context menu event on svg tag will be dispatched as custom event, the custom menu will not be opened
  // set to true, to start a custom action on right click, WILL WORK ONLY ON SVG TAG ITSELF FOR NOW
  public dispatchContextMenuEvent = false;
  // if true element can be dropped into the svg
  public allowDrop = true;
  // time in ms to do the polling for size changes of the svg (default: 100)
  public sizePollingTime = 100;
  // size of the offset when showing the entire workflow (works like padding in css) (default: 25)
  public showEntireWorkflowOffset = 25;
  // minimal zoom level when showing the entire workflow (default: 0.75 (150% Zoom Level))
  public showEntrieWorkflowMinZoom = 0.75;
  // list of element names that don't trigger a context menu (e.g. ['g', 'path', 'circle']) (default: [])
  public forceNonInteractiveContextMenu: string[] = [];
  // if true links can be modified (default: true)
  public allowLinkModification = true;
  // if true allow creation of links (default: true)
  public allowLinkCreation = true;
}

/**
 * creates a shallow copy of the configuration, set to be in a readonly state
 * @param config configuration that should be the base for the readonly state
 */
export function createReadOnlyConfig(
  config: SVGManipulatorConfiguration
): SVGManipulatorConfiguration {
  const readOnlyVersion = { ...config };
  readOnlyVersion.canMoveElements = false;
  readOnlyVersion.forceNonInteractiveContextMenu = ['g', 'path', 'circle'];
  readOnlyVersion.allowDrop = false;
  readOnlyVersion.allowLinkModification = false;
  readOnlyVersion.allowLinkCreation = false;
  return readOnlyVersion;
}
