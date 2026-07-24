import { isFlowchartComponent } from '../../hetida-flowchart';

// Explicit null type needed: without it the literal widens to an implicit any
// because strictNullChecks is disabled.
// eslint-disable-next-line @typescript-eslint/no-inferrable-types
const nullValue: null = null;
const emptyArray: unknown[] = [];

it('isFlowchartComponent Typeguard', () => {
  const sameAttributes = {
    uuid: 13,
    name: 13,
    revision: 12,
    inputs: 'hello',
    outputs: 'nope',
    pos_x: [{ x: 6 }],
    pos_y: { neun: 5 },
    type: 7,
    disabled: 0
  };

  const componentInvalid = {
    uuid: 'test',
    name: 'test',
    revision: 'test',
    inputs: emptyArray,
    outputs: emptyArray,
    pos_x: nullValue,
    pos_y: 5,
    type: 'WORKFLOW',
    disabled: true
  };

  const componentValid = {
    uuid: 'test',
    name: 'test',
    revision: 'test',
    inputs: emptyArray,
    outputs: emptyArray,
    pos_x: nullValue,
    pos_y: nullValue,
    type: 'WORKFLOW',
    disabled: true
  };

  const close = {
    uuid: 'test',
    name: 'test',
    revision: 'test',
    inputs: [
      {
        uuid: '7',
        data_type: '7',
        name: '7',
        input: true,
        pos_x: nullValue,
        pos_y: nullValue
      }
    ],
    outputs: emptyArray,
    pos_x: nullValue,
    pos_y: nullValue,
    type: 'COMPONENT',
    disabled: false
  };

  expect(isFlowchartComponent(sameAttributes)).toBe(false);
  expect(isFlowchartComponent(componentValid)).toBe(true);
  expect(isFlowchartComponent(close)).toBe(false);
  expect(isFlowchartComponent(componentInvalid)).toBe(false);
});
