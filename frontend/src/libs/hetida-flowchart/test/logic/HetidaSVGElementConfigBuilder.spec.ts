import { HetidaSVGElementConfigBuilder } from '../../logic/HetidaSVGElementConfigBuilder';
import { IOType } from '../../Types';

it('HetidaSVGElementConfigBuilder Init', () => {
  const config = new HetidaSVGElementConfigBuilder().build();
  expect(config.get('x')).toBe('0');
  expect(config.get('y')).toBe('0');
  expect(config.size).toBe(2);
});

function* randomNumberGenerator(max: number) {
  yield Math.random() * max;
  return 0;
}

function getRandomNumber(max: number): number {
  return randomNumberGenerator(max).next().value;
}

it('HetidaSVGElementConfigBuilder Width', () => {
  for (let i = 0; i < 10; i++) {
    const rng = getRandomNumber(1_000_000);
    const config = new HetidaSVGElementConfigBuilder().setWidth(rng).build();
    expect(config.get('width')).toBe(rng.toString());
  }
});

it('HetidaSVGElementConfigBuilder Height', () => {
  for (let i = 0; i < 10; i++) {
    const rng = getRandomNumber(1_000_000);
    const config = new HetidaSVGElementConfigBuilder().setHeight(rng).build();
    expect(config.get('height')).toBe(rng.toString());
  }
});

it('HetidaSVGElementConfigBuilder Points', () => {
  for (let i = 0; i < 10; i++) {
    const points: [number, number][] = [];
    const count = getRandomNumber(25);
    for (let p = 0; p < count; p++) {
      points.push([getRandomNumber(1_000_000), getRandomNumber(1_000_000)]);
    }
    const config = new HetidaSVGElementConfigBuilder()
      .setPoints(points)
      .build();

    const pointString = points.map(pair => pair.join(',')).join(' ');
    expect(config.get('points')).toBe(pointString);
  }
});

it('HetidaSVGElementConfigBuilder CSS Class', () => {
  const config = new HetidaSVGElementConfigBuilder()
    .setClass('test')
    .setClass('another')
    .setClass('really-specific-wierd-class')
    .build();
  expect(config.get('class')).toBe('test another really-specific-wierd-class');
});

it('HetidaSVGElementConfigBuilder ID', () => {
  const config = new HetidaSVGElementConfigBuilder().setId('test.uuid').build();
  expect(config.get('id')).toBe('test.uuid');
});

it('HetidaSVGElementConfigBuilder Link', () => {
  const inputConfig = new HetidaSVGElementConfigBuilder()
    .setLink(IOType.DATAFRAME, true, false)
    .build();

  const outputConfig = new HetidaSVGElementConfigBuilder()
    .setLink(IOType.ANY, false, false)
    .build();

  expect(inputConfig.get('dataType')).toBe(IOType.DATAFRAME);
  expect(inputConfig.get('class')).toBe('flowchart-input');

  expect(outputConfig.get('dataType')).toBe(IOType.ANY);
  expect(outputConfig.get('class')).toBe('flowchart-output');
});

it('HetidaSVGElementConfigBuilder Position', () => {
  for (let i = 0; i < 10; i++) {
    const x = getRandomNumber(1_000_000);
    const y = getRandomNumber(1_000_000);
    const config = new HetidaSVGElementConfigBuilder()
      .setPosition(x, y)
      .build();

    expect(config.get('x')).toBe(x.toString());
    expect(config.get('y')).toBe(y.toString());
  }
});

it('HetidaSVGElementConfigBuilder Dispatcher', () => {
  const ioDispatcherConfig = new HetidaSVGElementConfigBuilder()
    .setEventDispatcher(true, 'io')
    .build();
  const ioNonDispatcherConfig = new HetidaSVGElementConfigBuilder()
    .setEventDispatcher(false, 'io')
    .build();

  expect(ioDispatcherConfig.get('dispatcher')).toBe('io');
  expect(ioNonDispatcherConfig.get('dispatcher')).toBe(undefined);
});

it('HetidaSVGElementConfigBuilder Center Position', () => {
  for (let i = 0; i < 10; i++) {
    const x = getRandomNumber(1_000_000);
    const y = getRandomNumber(1_000_000);
    const config = new HetidaSVGElementConfigBuilder()
      .setCenterPosition(x, y)
      .build();

    expect(config.get('cx')).toBe(x.toString());
    expect(config.get('cy')).toBe(y.toString());
  }
});

it('HetidaSVGElementConfigBuilder Radius', () => {
  for (let i = 0; i < 10; i++) {
    const r = getRandomNumber(1_000_000);
    const config = new HetidaSVGElementConfigBuilder().setRadius(r).build();

    expect(config.get('r')).toBe(r.toString());
  }
});

it('HetidaSVGElementConfigBuilder Custom Attribute', () => {
  for (let i = 0; i < 10; i++) {
    const key = getRandomNumber(1_000_000).toString();
    const value = getRandomNumber(1_000_000);
    const config = new HetidaSVGElementConfigBuilder()
      .setCustomAttribute(key, value)
      .build();

    expect(config.get(key)).toBe(value.toString());
  }
});
