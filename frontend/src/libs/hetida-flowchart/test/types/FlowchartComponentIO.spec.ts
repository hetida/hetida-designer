import { isFlowchartComponentIO } from '../../Types';

// Explicit null type needed: without it the literal widens to an implicit any
// because strictNullChecks is disabled.
// eslint-disable-next-line @typescript-eslint/no-inferrable-types
const nullValue: null = null;

it('isFlowchartComponentIO Typeguard', () => {
  const sameAttributes = {
    uuid: 13,
    data_type: 89,
    name: { ts: 'yes' },
    input: 7.7,
    pos_x: [18290, 109283],
    pos_y: nullValue,
    constant: 8,
    value: { a: 8 }
  };
  const io = {
    uuid: 'test',
    data_type: 'BOOLEAN',
    name: 'test',
    input: false,
    pos_x: nullValue,
    pos_y: nullValue,
    constant: true,
    value: '17'
  };
  const ioInvalid = {
    uuid: 'test',
    data_type: 'BOOLEAN',
    name: 'test',
    input: false,
    pos_x: nullValue,
    pos_y: 7,
    constant: true,
    value: ''
  };
  const close = {
    uuid: 'test',
    data_type: 'FLAOT',
    name: 'test',
    input: false,
    pos_x: nullValue,
    pos_y: nullValue,
    constant: false,
    value: '{"ab":"78"}'
  };

  expect(isFlowchartComponentIO(sameAttributes)).toBe(false);
  expect(isFlowchartComponentIO(io)).toBe(true);
  expect(isFlowchartComponentIO(close)).toBe(false);
  expect(isFlowchartComponentIO(ioInvalid)).toBe(false);
});
