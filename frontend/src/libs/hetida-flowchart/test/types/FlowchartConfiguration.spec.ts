import { isFlowchartConfiguration } from '../../Types';

// Explicit null type needed: without it the literal widens to an implicit any
// because strictNullChecks is disabled.
// eslint-disable-next-line @typescript-eslint/no-inferrable-types
const nullValue: null = null;
const emptyArray: unknown[] = [];

it('isFlowchartConfiguration Typeguard', () => {
  const sameAttributes = {
    id: 5,
    components: 'abcd',
    io: 777,
    links: ['abc', 9, { z: 'fünf' }]
  };

  const config = {
    id: 'string',
    components: [
      {
        uuid: 'test',
        name: 'test',
        revision: 'test',
        inputs: emptyArray,
        outputs: [
          {
            uuid: 'test',
            data_type: 'BOOLEAN',
            name: 'test',
            input: false,
            pos_x: nullValue,
            pos_y: nullValue,
            constant: true,
            value: '{"a":8}'
          }
        ],
        pos_x: nullValue,
        pos_y: nullValue,
        type: 'WORKFLOW',
        disabled: true
      }
    ],
    io: [
      {
        uuid: 'test',
        data_type: 'BOOLEAN',
        name: 'test',
        input: false,
        pos_x: nullValue,
        pos_y: nullValue,
        constant: false,
        value: ''
      }
    ],
    links: [
      {
        uuid: 'test',
        from: 'test',
        to: 'test',
        path: [
          [5, 6],
          [19, 25],
          [800, 900]
        ],
        path_ids: ['x', 'y', 'z']
      }
    ]
  };

  const close = {
    id: 'string',
    components: [
      {
        uuid: 'test',
        name: 'test',
        revision: 'test',
        inputs: emptyArray,
        outputs: [
          {
            uuid: 'test',
            data_type: 'BOOLEAN',
            name: 'test',
            input: false,
            pos_x: 'null',
            pos_y: nullValue,
            constant: true,
            value: ''
          }
        ],
        pos_x: nullValue,
        pos_y: nullValue,
        disabled: false
      }
    ],
    io: [
      {
        uuid: 'test',
        data_type: 'BOOLEAN',
        name: 'test',
        input: false,
        pos_x: nullValue,
        pos_y: nullValue,
        constant: false,
        value: ''
      }
    ],
    links: [
      {
        uuid: 'test',
        from: 'test',
        to: 'test',
        path: [
          [5, 6],
          [19, 25],
          [800, 900]
        ],
        path_ids: ['x', 'y', 'z']
      }
    ]
  };

  expect(isFlowchartConfiguration(sameAttributes)).toBe(false);
  expect(isFlowchartConfiguration(config)).toBe(true);
  expect(isFlowchartConfiguration(close)).toBe(false);
});
