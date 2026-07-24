/**
 * Rounds a number keeping the sepcified amount of decimal places
 * @param value number to be rounded
 * @param decimals decimals to be kept
 */
export function roundWithDecimals(value: number, decimals: number): number {
  const numString = `${value.toString()}e+${decimals}`;
  const roundedOnce = Math.round(Number(numString));
  const numStringFinal = `${roundedOnce.toString()}e-${decimals}`;
  return Number(numStringFinal);
}

/**
 * checks wether the value is within the threshold to the target value
 * @param value value to be checked against target
 * @param target target value
 * @param threshold threshold the value can differ from target
 */
export function isCloseTo(
  value: number,
  target: number,
  threshold: number
): boolean {
  return Math.abs(value - target) <= threshold;
}

/**
 * checks wether the check coordinates are on the line through start and end
 * @param start x,y coordinates of the start point
 * @param end x,y coordinates of the end point
 * @param check x,y coordinates of the check point
 */
export function isOnLine(
  start: [number, number],
  end: [number, number],
  check: [number, number]
): boolean {
  const dxc = check[0] - start[0];
  const dyc = check[1] - start[1];

  const xcn = end[0] - start[0];
  const ycn = end[1] - start[1];

  const onLine = dxc * ycn - dyc * xcn;

  return isCloseTo(onLine, 0, 0.05);
}

/**
 * checks wether the x,y coordinates of both points are within the threshold to another
 * @param one first point
 * @param two second point
 * @param threshold threshold the values can differ
 */
export function checkIfCoordinatesAreClose(
  one: [number, number],
  two: [number, number],
  threshold: number
): boolean {
  return (
    isCloseTo(one[0], two[0], threshold) && isCloseTo(one[1], two[1], threshold)
  );
}

/**
 * Converts from 2d coordinates to a comma seperated sting
 * @param coordinates coordinates to be converted
 */
export function convertCooordinatesToCommaSeperatedString(
  coordinates: [number, number][]
): string {
  return coordinates.map(xy => xy.join(',')).join(' ');
}

/**
 * extracts the coordinates from a SVGPolygonElement and converts them to 2d coordinates
 * @param element SVGPolygonElement the coordinates should be extracted from
 */
export function getCoordinatesFromPolygon(
  element: SVGPolygonElement
): [number, number][] {
  const points = element.getAttribute('points');
  assert(points !== null, 'points attribute is undefined');
  return points
    .split(' ')
    .map(pair => pair.split(',').map(strCoord => Number(strCoord)))
    .map(cooridnates => [cooridnates[0], cooridnates[1]] as [number, number]);
}

/**
 * determines the position of the new anchor point according to the given x and y coordinates
 * @param x x coordinate of the new anchor
 * @param y y coordinate of the new anchor
 * @param coordinates coordinates of the path the anchor will be added to
 */
export function findPositionInCoordinates(
  x: number,
  y: number,
  coordinates: [number, number][]
): number | null {
  for (let i = 0; i < coordinates.length - 1; i++) {
    const currentAnchor = coordinates[i];
    const nextAnchor = coordinates[i + 1];
    if (isOnLine(currentAnchor, nextAnchor, [x, y])) {
      return i + 1;
    }
  }
  return null;
}

/**
 * Helper to find upper most parent svg element of the given element
 * @param element element the parent element should be determined for
 */
export function findParentElement(element: Element): Element {
  if (element.nodeName === 'svg') {
    if (
      element.parentElement === null ||
      element.parentElement.nodeName !== 'foreignObject'
    ) {
      return element;
    }
  }
  let parent = element.parentElement;
  if (parent === null) {
    return element;
  }
  if (parent.nodeName === 'svg') {
    return element;
  }
  while (true) {
    if (parent.parentElement === null) {
      break;
    }
    if (parent.parentElement.nodeName === 'svg') {
      break;
    }
    parent = parent.parentElement;
  }
  return parent;
}

/**
 * gets the coordinates from a path element
 * @param link path element
 */
export function getCoordinatesFromLink(link: Element): [number, number][] {
  const path = link.getAttribute('d');
  assert(path !== null, 'link undefined!');
  const values = path.split(' L '); // Format is 'M(x) (y) {L (x) (y)}*'
  values[0] = values[0].substr(1); // Format is 'M(x) (y) {L (x) (y)}*', we remove the M
  return values
    .map(pair =>
      pair
        .trim()
        .split(' ')
        .map(strCoord => Number(strCoord))
    )
    .map(coords => [coords[0], coords[1]]);
}

/**
 * formats the coordinates as path string
 * @param coordinates coordiantes to be converted
 */
export function createLinkFromCoordinates(coordinates: number[][]): string {
  const values = coordinates.map(coord => coord.join(' ')).join(' L ');
  return `M${values}`;
}

/**
 * gets the midpoint between the previous position and the given position for the given coordinates
 * @param position position the midpoints to the previous position should be returned
 * @param coordinates given coordinates
 */
export function getMidpointForPosition(
  position: number,
  coordinates: [number, number][]
): [number, number] {
  assert(
    position !== 0 && position < coordinates.length,
    'Invalid position in coordinates'
  );
  return [
    (coordinates[position - 1][0] + coordinates[position][0]) / 2,
    (coordinates[position - 1][1] + coordinates[position][1]) / 2
  ];
}

/**
 * find all links for a given io id
 * @param linkId id of an element that is part of the link
 */
export function findAllLinksForIO(
  ioID: string,
  svg: SVGSVGElement
): SVGPathElement[] {
  const links: SVGPathElement[] = [];
  for (const child of svg.getElementsByTagName('path')) {
    const startId = child.getAttribute('link-start');
    const endId = child.getAttribute('link-end');
    if (startId === ioID || endId === ioID) {
      links.push(child);
    }
  }
  return links;
}

/**
 * helper to find cycles in the element graph
 * @param start element we if it is already the destionation or if it's children connect it to the destination
 * @param destination element that would end the cycle
 */
export function checkForCycle(
  start: Element,
  destination: Element,
  svg: SVGSVGElement
): boolean {
  const startOutputs = Array.from(
    start.getElementsByClassName('flowchart-output')
  );
  // no outputs, no further checking needed
  if (startOutputs.length === 0) {
    return false;
  }
  // if any of the outputs of the element is the target, stop here
  if (startOutputs.some(output => output.id === destination.id)) {
    return true;
  }
  // check every output depth first
  for (const output of startOutputs) {
    // we have a output element, check if it has a connected link
    const links = findAllLinksForIO(output.id, svg);
    for (const link of links) {
      const linkTargetId = link.getAttribute('link-end');
      if (linkTargetId === null) {
        continue;
      }
      const linkTarget = svg.getElementById(linkTargetId);
      if (linkTarget === null) {
        continue;
      }
      // get parent of link target
      const linkParent = findParentElement(linkTarget);
      if (checkForCycle(linkParent, destination, svg)) {
        return true;
      }
    }
  }
  return false;
}

export function assert(condition: boolean, msg: string): asserts condition {
  if (condition === false) {
    throw new Error(`[Assertion Violation]: ${msg}`);
  }
}
