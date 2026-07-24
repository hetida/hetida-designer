import { isFlowchartComponentLink } from '../../hetida-flowchart';

// Explicit null type needed: without it the literal widens to an implicit any
// because strictNullChecks is disabled.
// eslint-disable-next-line @typescript-eslint/no-inferrable-types
const nullValue: null = null;

it('isFlowchartComponentLink Typeguard', () => {
  const sameAttributes = {
    uuid: 13,
    from: 89,
    to: { ts: 'yes' },
    path: 7.7,
    path_ids: [18290, 109283]
  };

  const link = {
    uuid: 'test',
    from: 'test',
    to: 'test',
    path: [
      [8, 9],
      [221, 2394]
    ],
    path_ids: ['test', 'test2']
  };

  const defaultLink = {
    uuid: 'test',
    from: 'test',
    to: 'test',
    path: nullValue,
    path_ids: ['test']
  };

  const linkTest = {
    uuid: 'test',
    from: 'test',
    to: 'test',
    path: [
      [8, 9],
      [221, 2394]
    ],
    path_ids: ['test']
  };

  const close = {
    uuid: 'test',
    from: 'test',
    to: 'test',
    path: [
      [8, '9'],
      [221, 2394]
    ],
    path_ids: ['test']
  };

  expect(isFlowchartComponentLink(sameAttributes)).toBe(false);
  expect(isFlowchartComponentLink(link)).toBe(true);
  expect(isFlowchartComponentLink(close)).toBe(false);
  expect(isFlowchartComponentLink(defaultLink)).toBe(false);
  expect(isFlowchartComponentLink(linkTest)).toBe(false);
});
