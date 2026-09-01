import {
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
} from '../../logic/SVGHelper';

it('SVGHelper roundWithDecimals', () => {
  expect(roundWithDecimals(1.056, 2)).toEqual(1.06);
  expect(roundWithDecimals(1.054, 2)).toEqual(1.05);
  expect(roundWithDecimals(1.05, 1)).toEqual(1.1);
});

it('SVGHelper isCloseTo', () => {
  expect(isCloseTo(0.5, 0.6, 0.1)).toBe(true);
  expect(isCloseTo(0.5, 0.75, 0.2)).toBe(false);
  expect(isCloseTo(123, 200, 80)).toBe(true);
});

it('SVGHelper convertCooordinatesToCommaSeperatedString', () => {
  const coordinates: [number, number][] = [
    [8, 9],
    [239, 2323],
    [12, 65]
  ];
  expect(convertCooordinatesToCommaSeperatedString(coordinates)).toBe(
    '8,9 239,2323 12,65'
  );
});

it('SVGHelper getCoordinatesFromPolygon', () => {
  const polygon = window.document.createElementNS(
    'http://www.w3.org/2000/svg',
    'polygon'
  );
  polygon.setAttribute('points', '15,16 132,234 2342,9999');
  expect(getCoordinatesFromPolygon(polygon)).toEqual([
    [15, 16],
    [132, 234],
    [2342, 9999]
  ]);
});

it('SVGHelper findPositionInCoordinates', () => {
  const coordinates: [number, number][] = [
    [1230, 12],
    [8, 9],
    [12, 18],
    [0, 60]
  ];
  expect(findPositionInCoordinates(10, 13.5, coordinates)).toBe(2);
  expect(findPositionInCoordinates(6, 39, coordinates)).toBe(3);
  expect(findPositionInCoordinates(1, 56.5, coordinates)).toBe(3);
  expect(findPositionInCoordinates(1, 1, coordinates)).toBe(null);
});

it('SVGHelper findParentElement', () => {
  const svg = window.document.createElementNS(
    'http://www.w3.org/2000/svg',
    'svg'
  ) as Element;
  const g = window.document.createElementNS(
    'http://www.w3.org/2000/svg',
    'g'
  ) as Element;
  const rect = window.document.createElementNS(
    'http://www.w3.org/2000/svg',
    'rect'
  ) as Element;
  (window.document.body as Element).appendChild(svg);
  svg.appendChild(g);
  g.appendChild(rect);

  expect(findParentElement(svg)).toBe(svg);
  expect(findParentElement(g)).toBe(g);
  expect(findParentElement(rect)).toBe(g);

  svg.remove();
});

it('SVGHelper getCoordinatesFromLink', () => {
  const link = window.document.createElement('path');
  link.setAttribute('d', 'M17 18 L 9999 21 L 2482 2394 L 123 1203');

  expect(getCoordinatesFromLink(link)).toEqual([
    [17, 18],
    [9999, 21],
    [2482, 2394],
    [123, 1203]
  ]);
});

it('SVGHelper createLinkFromCoordinates', () => {
  const coordinates = [
    [17, 18],
    [3859, 293],
    [231, 0],
    [0, 23],
    [93, 153]
  ];
  expect(createLinkFromCoordinates(coordinates)).toBe(
    'M17 18 L 3859 293 L 231 0 L 0 23 L 93 153'
  );
});

it('SVGHelper getMidpointForPosition', () => {
  const coordinates: [number, number][] = [
    [17, 18],
    [3859, 293],
    [231, 0],
    [0, 23],
    [93, 153]
  ];
  expect(getMidpointForPosition(1, coordinates)).toEqual([1938, 155.5]);
  expect(getMidpointForPosition(4, coordinates)).toEqual([46.5, 88]);

  expect(() => getMidpointForPosition(0, coordinates)).toThrow();
  expect(() => getMidpointForPosition(19, coordinates)).toThrow();
});

it('SVGHelper isOnLine', () => {
  const start: [number, number] = [5, 193];
  const end: [number, number] = [25, 234];
  const onLine: [number, number] = [15, 213.5];
  const notOnLine: [number, number] = [20, 50];
  const onLineSecond: [number, number] = [30, 244.25];

  expect(isOnLine(start, end, onLine)).toBe(true);
  expect(isOnLine(start, end, notOnLine)).toBe(false);
  expect(isOnLine(start, end, onLineSecond)).toBe(true);
});

it('SVGHelper checkIfCoordinatesAreClose', () => {
  const one: [number, number] = [5, 6];
  const two: [number, number] = [6, 7];
  const three: [number, number] = [5.005, 6.00000000007];

  expect(checkIfCoordinatesAreClose(one, two, 1)).toBe(true);
  expect(checkIfCoordinatesAreClose(one, two, 1.01)).toBe(true);
  expect(checkIfCoordinatesAreClose(one, two, 0.5)).toBe(false);
  expect(checkIfCoordinatesAreClose(one, three, 0.05)).toBe(true);
});

it('SVGHelper findAllLinksForIO', () => {
  const svg = window.document.createElementNS(
    'http://www.w3.org/2000/svg',
    'svg'
  );
  const ids = [
    'test',
    'abc',
    'some',
    'def',
    '9',
    'fiask',
    '854',
    '12637',
    'ttttteeeee',
    'hd'
  ];
  // shuffle ids
  for (let i = ids.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    const x = ids[i];
    ids[i] = ids[j];
    ids[j] = x;
  }
  for (let i = 0; i < 5; i++) {
    const path = window.document.createElementNS(
      'http://www.w3.org/2000/svg',
      'path'
    ) as Element;
    path.setAttribute('link-start', ids[i * 2]);
    path.setAttribute('link-end', ids[i * 2 + 1]);
    svg.appendChild(path);
  }

  for (const id of ids) {
    expect(findAllLinksForIO(id, svg).length === 1).toBe(true);
  }
});

it('SVGHelper checkForCycle');
